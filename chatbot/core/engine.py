"""
The `Chatbot` class is the single entry point for using the template
programmatically. Channels (CLI, FastAPI, WhatsApp, Telegram, LINE) all
delegate to it.

Lifecycle:
    1. Construct from a `ChatbotProfile` and `Settings`.
    2. On construction, build the LLM, RAG retriever, and LangChain chain.
    3. Each `ask(...)` call sanitizes input, checks budgets, retrieves
       context, runs the chain, persists memory, records token usage.
"""

from __future__ import annotations

import re
import time
from typing import Any, Optional

from pydantic import BaseModel, Field

from chatbot.core.fallback_log import FallbackLog, looks_like_fallback
from chatbot.core.handoff import HandoffManager
from chatbot.core.memory import SessionStore
from chatbot.core.products import ProductCatalog
from chatbot.core.profile import ChatbotProfile
from chatbot.exceptions import (
    AbuseError,
    BudgetError,
    ChatbotError,
    LLMError,
    explain_llm_error,
)
from chatbot.llm.chains import build_rag_chain
from chatbot.llm.providers import LLMProvider
from chatbot.logging_setup import logger
from chatbot.rag.retriever import RAGRetriever
from chatbot.security.budget import BudgetExceeded, BudgetGuard, estimate_tokens
from chatbot.security.sanitize import (
    looks_like_prompt_injection,
    sanitize_session_id,
    sanitize_user_input,
)
from chatbot.security.spam import SpamTracker
from chatbot.settings import Settings, get_settings


# ── Handoff keyword detection ───────────────────────────────────────────────
# Phrases that indicate the user wants to talk to a human. Checked with
# simple substring matching (case-insensitive) before any paid LLM call.
_HANDOFF_PATTERNS = re.compile(
    r"(?i)"
    r"(?:"
    # English
    r"talk to (?:a |an )?(?:human|person|someone|agent|staff|representative|support)"
    r"|speak (?:to|with) (?:a |an )?(?:human|person|someone|agent|staff|representative|support)"
    r"|connect me (?:to|with) (?:a |an )?(?:human|person|someone|agent|staff|representative)"
    r"|transfer (?:me )?to (?:a |an )?(?:human|agent|staff|person|representative|support)"
    r"|i (?:want|need) (?:a |to talk to (?:a )?)?(?:human|real person|agent|staff|representative)"
    r"|(?:get|give) me (?:a )?(?:human|real person|agent|staff)"
    r"|can i (?:talk|speak|chat) (?:to|with) (?:a )?(?:human|person|someone|agent)"
    r"|let me (?:talk|speak|chat) (?:to|with) (?:a )?(?:human|person|someone|agent)"
    # Hebrew
    r"|לדבר עם (?:נציג|אדם|מישהו|תמיכה)"
    r"|תעביר(?:ו)? (?:ל)?נציג"
    r"|אני רוצה (?:לדבר עם )?(?:נציג|אדם|מישהו)"
    r"|(?:אפשר|אני צריך) (?:לדבר עם )?(?:נציג|אדם|מישהו)"
    # Thai
    r"|(?:ขอ)?(?:คุย|พูด)กับ(?:คน|เจ้าหน้าที่|พนักงาน|แอดมิน)"
    r"|ต้องการ(?:คุย|พูด)กับ(?:คน|เจ้าหน้าที่|พนักงาน)"
    r"|ขอติดต่อ(?:เจ้าหน้าที่|พนักงาน|แอดมิน)"
    # Arabic
    r"|(?:أريد|اريد) (?:التحدث|الكلام) (?:مع|إلى) (?:شخص|موظف|ممثل)"
    r"|(?:حوّلني|حولني) (?:إلى|الى) (?:شخص|موظف|ممثل)"
    # Russian
    r"|(?:хочу|могу) поговорить с (?:человеком|оператором|агентом)"
    r"|(?:переведите|переключите) (?:на|к) (?:человеку|оператору|агенту)"
    r")"
)


def _channel_from_session(session_id: str) -> str:
    """Extract channel name from a session ID prefix."""
    if session_id.startswith("line:"):
        return "line"
    if session_id.startswith("telegram:"):
        return "telegram"
    if session_id.startswith("whatsapp:"):
        return "whatsapp"
    return "web"


class SourceDocument(BaseModel):
    """A retrieved document chunk surfaced as a source citation."""

    source: str
    page: Optional[int] = None
    snippet: str = ""
    score: Optional[float] = None


class ChatResponse(BaseModel):
    """Structured response returned by `Chatbot.ask`."""

    answer: str
    session_id: str
    sources: list[SourceDocument] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Chatbot:
    """High-level orchestrator: profile + memory + RAG + LLM + budget."""

    def __init__(
        self,
        profile: ChatbotProfile,
        settings: Optional[Settings] = None,
        *,
        retriever: Optional[RAGRetriever] = None,
        llm: Optional[LLMProvider] = None,
        memory: Optional[SessionStore] = None,
        budget: Optional[BudgetGuard] = None,
        spam_tracker: Optional[SpamTracker] = None,
        product_catalog: Optional[ProductCatalog] = None,
        handoff_manager: Optional[HandoffManager] = None,
        fallback_log: Optional[FallbackLog] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.profile = profile

        logger.info(
            "Initializing Chatbot client='{}' personality='{}' model='{}'",
            profile.client.id,
            profile.personality.name,
            self.settings.llm_model,
        )

        # Subsystems (allow injection for tests / advanced use)
        self.memory = memory or SessionStore.from_settings(self.settings)
        self.retriever = retriever or RAGRetriever.from_settings(self.settings)
        self.llm = llm or LLMProvider.from_settings(
            self.settings,
            temperature_override=profile.personality.temperature,
        )
        self.budget = budget or BudgetGuard(
            state_file=self.settings.budget_state_file,
            daily_token_cap=self.settings.daily_token_cap,
            daily_usd_cap=self.settings.daily_usd_cap,
            model=self.settings.llm_model,
            price_in_usd_per_1k=(
                self.settings.price_in_usd_per_1k or None
            ),
            price_out_usd_per_1k=(
                self.settings.price_out_usd_per_1k or None
            ),
        )

        # Spam / gibberish tracker — applies to all channels via ask().
        if spam_tracker is not None:
            self.spam_tracker: SpamTracker | None = spam_tracker
        elif self.settings.spam_detection_enabled:
            self.spam_tracker = SpamTracker(
                max_strikes=self.settings.spam_max_strikes,
                cooldown_seconds=self.settings.spam_cooldown_seconds,
                max_cooldown_seconds=self.settings.spam_max_cooldown_seconds,
                min_meaningful_chars=self.settings.spam_min_message_chars,
            )
        else:
            self.spam_tracker = None

        # ── Product catalog ────────────────────────────────────────────
        self.product_catalog = product_catalog or ProductCatalog.load(
            profile.client.id
        )

        # ── Human handoff ──────────────────────────────────────────────
        self.handoff = handoff_manager or HandoffManager()

        # ── Fallback logger ────────────────────────────────────────────
        self.fallback_log = fallback_log or FallbackLog()

        # Build the LangChain RAG chain once
        self.chain = build_rag_chain(
            llm=self.llm.client,
            retriever=self.retriever.as_langchain_retriever(),
            system_prompt=profile.effective_system_prompt,
        )

        if self.budget.enabled:
            logger.info(
                "Budget guard active: tokens/day={} usd/day={}",
                self.settings.daily_token_cap,
                self.settings.daily_usd_cap,
            )

        logger.info("Chatbot ready: {}", profile.client.name)

    # ── Public API ──────────────────────────────────────────────────────────

    def ask(
        self,
        question: str,
        session_id: str = "default",
        *,
        language: Optional[str] = None,
    ) -> ChatResponse:
        """Run a single chat turn and return a structured response.

        Parameters
        ----------
        question:
            Raw user message. Will be sanitized and length-checked.
        session_id:
            Stable per-user identifier (channel:user_id, web tab id, ...).
        language:
            Optional ISO-639-1 hint for the reply language. The engine
            passes this into the system prompt at request time so the
            visitor can switch languages without rebuilding the chain.

        Validation order is intentional: cheapest checks first so abusive
        traffic is rejected before it costs anything.

        1. Sanitize the session id (cheap).
        2. Sanitize and length-check the question (cheap, no LLM).
        3. Spam / gibberish check (cheap, string comparisons only).
        4. Estimate input tokens and check the daily budget guard
           (cheap, blocks before any paid call).
        5. Run the LangChain RAG chain (paid).
        6. Persist memory + collect sources for citation.
        7. Record actual token usage in the budget guard.
        """
        session_id = sanitize_session_id(session_id)

        # 1+2. Sanitize input.
        try:
            question = sanitize_user_input(
                question, max_chars=self.settings.max_message_chars
            )
        except ValueError as exc:
            logger.info("[{}] Rejected message: {}", session_id, exc)
            raise AbuseError(str(exc), user_message=str(exc)) from exc

        if looks_like_prompt_injection(question):
            logger.warning(
                "[{}] Prompt-injection markers in user input (first 80 chars): {!r}",
                session_id,
                question[:80],
            )
            if self.settings.block_prompt_injection:
                raise AbuseError(
                    "Prompt injection detected",
                    user_message="I can only answer questions about our business. Please rephrase your question.",
                )

        logger.debug("[{}] User message received ({} chars)", session_id, len(question))

        # 3a. Handoff check: if session is in human-handoff mode, queue
        #     the message for the admin and return a waiting response.
        if self.settings.handoff_enabled and self.handoff.is_handed_off(session_id):
            self.handoff.add_message(session_id, "user", question)
            # Check for a pending admin reply to deliver back.
            admin_reply = self.handoff.get_pending_admin_reply(session_id)
            if admin_reply:
                return ChatResponse(
                    answer=admin_reply,
                    session_id=session_id,
                    sources=[],
                    metadata={"handoff": True, "from_admin": True},
                )
            return ChatResponse(
                answer="A human agent is reviewing your conversation. Please wait for a reply.",
                session_id=session_id,
                sources=[],
                metadata={"handoff": True},
            )

        # 3b. User-initiated handoff: detect phrases like "talk to a human".
        #     This runs BEFORE the (paid) LLM call to save cost.
        if self.settings.handoff_enabled and _HANDOFF_PATTERNS.search(question):
            channel = _channel_from_session(session_id)
            self.handoff.start_handoff(session_id, channel=channel, reason="user_request")
            self.handoff.add_message(session_id, "user", question)
            logger.info("[{}] User-initiated handoff (channel={})", session_id, channel)
            return ChatResponse(
                answer="I'm connecting you with our team now. A human agent will be with you shortly — please wait.",
                session_id=session_id,
                sources=[],
                metadata={"handoff": True, "handoff_started": True},
            )

        # 3b. Spam / gibberish check (all channels).
        if self.spam_tracker is not None:
            rejection = self.spam_tracker.check(session_id, question)
            if rejection:
                logger.info("[{}] Spam blocked: {}", session_id, rejection)
                raise AbuseError(rejection, user_message=rejection)

        history = self.memory.history_text(session_id)

        # 4. Budget pre-check (estimate is intentionally pessimistic).
        est_in = estimate_tokens(question + (history or ""))
        try:
            self.budget.check_can_spend(est_in)
        except BudgetExceeded as exc:
            logger.warning("[{}] Budget exceeded: {}", session_id, exc.reason)
            raise BudgetError(exc.reason) from exc

        # 5. The actual paid LLM call with retry for transient failures.
        catalog_text = self.product_catalog.for_system_prompt()
        system_prompt = self.profile.build_system_prompt(
            language=language, product_catalog_text=catalog_text,
        )
        invoke_input = {
            "question": question,
            "history": history or "(no prior conversation)",
            "system_prompt": system_prompt,
        }
        answer: str = self._invoke_with_retry(invoke_input, session_id)

        # 6. Persist memory
        self.memory.add_message(session_id, "user", question)
        self.memory.add_message(session_id, "assistant", answer)

        # 6b. Log fallback if the bot couldn't answer
        if looks_like_fallback(answer):
            from chatbot.core.fallback_log import FallbackEntry
            self.fallback_log.log(FallbackEntry(
                question=question,
                answer_given=answer,
                session_id=session_id,
                language=language or "",
            ))

        # Do not trigger a second retrieval here. The RAG chain already
        # performs retrieval internally, and a second lookup can both add
        # unnecessary cost and return citations that do not match the
        # context actually used to generate `answer`.
        sources = []

        # 7. Record actual usage. We re-estimate from the strings because
        # not all providers expose .usage_metadata uniformly.
        try:
            self.budget.record(
                input_tokens=est_in,
                output_tokens=estimate_tokens(answer),
            )
        except Exception as exc:  # never let metering crash a reply
            logger.warning("[{}] budget.record failed: {}", session_id, exc)

        logger.debug(
            "[{}] Bot reply ({} chars)",
            session_id,
            len(answer),
        )

        # Detect products mentioned in the answer for image delivery
        mentioned = self.product_catalog.find_mentioned(answer)
        metadata: dict[str, Any] = {}
        if mentioned:
            metadata["products"] = [
                {"id": p.id, "name": p.name, "name_en": p.name_en,
                 "image_url": p.image_url, "price": p.price}
                for p in mentioned
            ]

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            sources=sources,
            metadata=metadata,
        )

    def greet(self) -> str:
        return self.profile.greeting

    def reset(self, session_id: str) -> None:
        """Forget a single conversation."""
        session_id = sanitize_session_id(session_id)
        self.memory.clear(session_id)
        logger.info("Cleared session: {}", session_id)

    # ── Helpers ─────────────────────────────────────────────────────────────

    _LLM_MAX_RETRIES = 2
    _LLM_RETRY_BACKOFF = 1.0  # seconds; doubles each attempt

    def _invoke_with_retry(self, invoke_input: dict, session_id: str) -> str:
        """Call the LLM chain with exponential-backoff retry on transient errors."""
        last_exc: Exception | None = None
        for attempt in range(self._LLM_MAX_RETRIES + 1):
            try:
                return self.chain.invoke(invoke_input)
            except ChatbotError:
                raise
            except Exception as exc:
                last_exc = exc
                text = str(exc).lower()
                is_transient = any(k in text for k in ("429", "rate_limit", "timeout", "connection"))
                if not is_transient or attempt == self._LLM_MAX_RETRIES:
                    friendly = explain_llm_error(exc)
                    logger.exception("[{}] LLM call failed: {}", session_id, exc)
                    raise LLMError(friendly, user_message=friendly) from exc
                wait = self._LLM_RETRY_BACKOFF * (2 ** attempt)
                logger.warning(
                    "[{}] LLM transient error (attempt {}/{}), retrying in {:.1f}s: {}",
                    session_id, attempt + 1, self._LLM_MAX_RETRIES + 1, wait, exc,
                )
                time.sleep(wait)
        # Should not reach here, but just in case
        friendly = explain_llm_error(last_exc) if last_exc else "LLM call failed"
        raise LLMError(friendly, user_message=friendly)

    def _build_sources(self, docs: list) -> list[SourceDocument]:
        """Convert retrieved documents to source citations."""
        out: list[SourceDocument] = []
        for d in docs:
            md = d.metadata or {}
            out.append(
                SourceDocument(
                    source=str(md.get("source") or md.get("file_name") or "unknown"),
                    page=md.get("page"),
                    snippet=(d.page_content or "")[:200],
                )
            )
        return out

    def _collect_sources(self, question: str) -> list[SourceDocument]:
        try:
            docs = self.retriever.retrieve(question)
        except Exception as e:
            logger.warning("Failed to collect sources: {}", e)
            return []
        return self._build_sources(docs)

    # ── Constructors ────────────────────────────────────────────────────────

    @classmethod
    def from_client(
        cls, client_id: str, settings: Optional[Settings] = None
    ) -> Chatbot:
        """Build a Chatbot from a YAML client config under `config/clients/`."""
        from chatbot.settings import PROJECT_ROOT

        profile = ChatbotProfile.load(client_id)
        s = settings or get_settings()

        # Honour the client's data_paths so only its data is ingested.
        if profile.client.data_paths:
            s.data_dir = PROJECT_ROOT / profile.client.data_paths[0]

        return cls(profile=profile, settings=s)

    @classmethod
    def from_env(cls) -> Chatbot:
        """Build a Chatbot using `settings.active_client` (default: 'default')."""
        s = get_settings()
        return cls.from_client(s.active_client, settings=s)
