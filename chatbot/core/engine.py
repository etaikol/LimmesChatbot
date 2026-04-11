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
from chatbot.core.ab_testing import ABTestManager
from chatbot.core.analytics import AnalyticsTracker
from chatbot.core.feedback import FeedbackStore
from chatbot.core.user_memory import UserMemoryStore
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
from chatbot.i18n.messages import get_messages
from chatbot.security.spam import SpamTracker
from chatbot.settings import Settings, get_settings


# ── Handoff keyword detection ───────────────────────────────────────────────
# Phrases that indicate the user wants to talk to a human. Checked with
# simple substring matching (case-insensitive) before any paid LLM call.
#
# The keyword list is intentionally broad — false positives are cheap (the
# user just gets the handoff message) while false negatives cost a wasted
# LLM call *and* the user never reaches a human.

_HUMAN_WORDS = (
    r"human|person|some?one|anybody|people|agent|staff|representative|support"
    r"|manager|prof\w+al|expert|advisor|specialist|boss|owner"
    r"|real person|real human|live agent|live person|live chat"
)

_HANDOFF_PATTERNS = re.compile(
    r"(?i)"
    r"(?:"
    # ── English ──────────────────────────────────────────────────
    # "talk/speak/chat to/with a human/agent/professional/..."
    r"(?:talk|speak|chat|communicate)\s+(?:to|with)\s+(?:a\s+|an\s+)?(?:" + _HUMAN_WORDS + r")"
    # "connect/transfer/put me to/with a ..."
    r"|(?:connect|transfer|put|redirect|switch|escalate)\s+(?:me\s+)?(?:to|with)\s+(?:a\s+|an\s+)?(?:" + _HUMAN_WORDS + r")"
    # "i want/need/would like to talk to ..."
    r"|i\s+(?:want|need|would like|wanna|gotta)\s+(?:to\s+)?(?:talk|speak|chat|communicate)\s+(?:to|with)\s+(?:a\s+|an\s+)?(?:" + _HUMAN_WORDS + r")"
    # "i want/need a human/agent/representative"
    r"|i\s+(?:want|need|would like)\s+(?:a\s+|an\s+)?(?:" + _HUMAN_WORDS + r")"
    # "can/could/may i talk/speak/chat to/with ..."
    r"|(?:can|could|may)\s+i\s+(?:talk|speak|chat)\s+(?:to|with)\s+(?:a\s+|an\s+)?(?:" + _HUMAN_WORDS + r")"
    # "let me talk/speak to ..."
    r"|let\s+me\s+(?:talk|speak|chat)\s+(?:to|with)\s+(?:a\s+|an\s+)?(?:" + _HUMAN_WORDS + r")"
    # "get/give me a human/agent"
    r"|(?:get|give)\s+me\s+(?:a\s+|an\s+)?(?:" + _HUMAN_WORDS + r")"
    # "is there someone/anyone i can talk to"
    r"|is\s+there\s+(?:someone|anyone|somebody|a\s+person|a\s+human)\s+(?:i\s+can\s+(?:talk|speak|chat)\s+(?:to|with))?"
    # "can someone contact/reach/call me"
    r"|(?:can|could)\s+(?:someone|anyone|somebody)\s+(?:contact|reach|call|message|get back to)\s+me"
    # "i(?:'d| would) like to speak with ..."
    r"|i(?:'d|\s+would)\s+like\s+to\s+(?:talk|speak|chat)\s+(?:to|with)\s+(?:a\s+|an\s+)?(?:" + _HUMAN_WORDS + r")"
    # "no bot" / "not a bot" / "stop bot"
    r"|(?:no|not|stop)\s+(?:a\s+)?bot"

    # ── Hebrew ───────────────────────────────────────────────────
    r"|לדבר\s+עם\s+(?:נציג|אדם|מישהו|תמיכה|מנהל|מומחה|איש מקצוע)"
    r"|תעביר(?:ו)?\s+(?:ל)?נציג"
    r"|אני\s+רוצה\s+(?:לדבר\s+עם\s+)?(?:נציג|אדם|מישהו|מנהל)"
    r"|(?:אפשר|אני\s+צריך)\s+(?:לדבר\s+עם\s+)?(?:נציג|אדם|מישהו)"
    r"|(?:יש|אפשר)\s+(?:פה\s+)?מישהו\s+(?:לדבר\s+)?(?:איתו|עם)?"

    # ── Thai ─────────────────────────────────────────────────────
    r"|(?:ขอ)?(?:คุย|พูด|ติดต่อ|สนทนา)(?:กับ)?(?:คน|เจ้าหน้าที่|พนักงาน|แอดมิน|ผู้จัดการ|ผู้เชี่ยวชาญ)"
    r"|ต้องการ(?:คุย|พูด|ติดต่อ)(?:กับ)?(?:คน|เจ้าหน้าที่|พนักงาน)"
    r"|ขอติดต่อ(?:เจ้าหน้าที่|พนักงาน|แอดมิน|ผู้จัดการ)"
    r"|มีใคร(?:ให้|ที่)?(?:คุย|ปรึกษา|ติดต่อ)(?:ได้)?"
    r"|ขอ(?:คุย|พูด)กับ(?:คน|ทีม)"

    # ── Arabic ───────────────────────────────────────────────────
    r"|(?:أريد|اريد)\s+(?:التحدث|الكلام)\s+(?:مع|إلى)\s+(?:شخص|موظف|ممثل)"
    r"|(?:حوّلني|حولني)\s+(?:إلى|الى)\s+(?:شخص|موظف|ممثل)"

    # ── Russian ──────────────────────────────────────────────────
    r"|(?:хочу|могу)\s+поговорить\s+с\s+(?:человеком|оператором|агентом)"
    r"|(?:переведите|переключите)\s+(?:на|к)\s+(?:человеку|оператору|агенту)"
    r")"
)


def _spam_msg(key: str, language: str | None = None) -> str:
    """Return a localised human-friendly message for a spam/status *key*.

    *key* may be a plain i18n key (e.g. ``"handoff_waiting"``) or a
    structured spam-tracker reference like ``"spam:gibberish"`` or
    ``"spam:session_blocked:30"``.
    """
    msgs = get_messages(language or "en")
    if key.startswith("spam:"):
        parts = key.split(":")
        sub = parts[1] if len(parts) > 1 else ""
        secs = parts[2] if len(parts) > 2 else "0"
        if sub in ("blocked_temporarily", "session_blocked"):
            template = msgs.get(sub, "")
            if template:
                return template.replace("{seconds}", secs)
            return f"Please try again in {secs} seconds."
        return msgs.get(sub, key)
    return msgs.get(key, key)


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
        ab_test_manager: Optional[ABTestManager] = None,
        analytics_tracker: Optional[AnalyticsTracker] = None,
        feedback_store: Optional[FeedbackStore] = None,
        user_memory_store: Optional[UserMemoryStore] = None,
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

        # ── A/B testing ────────────────────────────────────────────────
        if ab_test_manager is not None:
            self.ab_test = ab_test_manager
        elif self.settings.ab_testing_enabled:
            self.ab_test = ABTestManager.from_config(profile.client.id)
        else:
            self.ab_test = None

        # ── Analytics tracker ──────────────────────────────────────────
        if analytics_tracker is not None:
            self.analytics: AnalyticsTracker | None = analytics_tracker
        elif self.settings.analytics_enabled:
            self.analytics = AnalyticsTracker()
        else:
            self.analytics = None

        # ── Feedback store ─────────────────────────────────────────────
        if feedback_store is not None:
            self.feedback: FeedbackStore | None = feedback_store
        elif self.settings.feedback_enabled:
            self.feedback = FeedbackStore()
        else:
            self.feedback = None

        # ── Long-term user memory ──────────────────────────────────────
        if user_memory_store is not None:
            self.user_memory: UserMemoryStore | None = user_memory_store
        elif self.settings.user_memory_enabled:
            self.user_memory = UserMemoryStore()
        else:
            self.user_memory = None

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
                    user_message=_spam_msg("off_topic", language),
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
                answer=_spam_msg("handoff_waiting", language),
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
            msg = _spam_msg("handoff_connecting", language)
            return ChatResponse(
                answer=msg,
                session_id=session_id,
                sources=[],
                metadata={"handoff": True, "handoff_started": True},
            )

        # 3c. Spam / gibberish check (all channels).
        if self.spam_tracker is not None:
            rejection = self.spam_tracker.check(session_id, question)
            if rejection:
                logger.info("[{}] Spam blocked: {}", session_id, rejection)
                msg = _spam_msg(rejection, language)
                raise AbuseError(rejection, user_message=msg)

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

        # 5a. A/B test variant: may override the personality
        ab_variant_name = ""
        active_profile = self.profile
        if self.ab_test and self.ab_test.enabled:
            variant = self.ab_test.assign(session_id)
            if variant:
                ab_variant_name = variant.name
                if variant.personality != self.profile.personality.name:
                    try:
                        from chatbot.core.profile import PersonalityConfig
                        alt_personality = PersonalityConfig.load(variant.personality)
                        active_profile = self.profile.model_copy()
                        active_profile.personality = alt_personality
                    except Exception as e:
                        logger.warning("[ab] Could not load variant personality: {}", e)

        # 5b. Long-term user memory context
        user_memory_text = ""
        if self.user_memory:
            channel = _channel_from_session(session_id)
            self.user_memory.record_interaction(
                session_id,
                question=question,
                language=language or "",
                channel=channel,
            )
            user_memory_text = self.user_memory.get_prompt_context(session_id)

        system_prompt = active_profile.build_system_prompt(
            language=language, product_catalog_text=catalog_text,
        )
        if user_memory_text:
            system_prompt = system_prompt + "\n\n" + user_memory_text

        _ask_start = time.time()
        invoke_input = {
            "question": question,
            "history": history or "(no prior conversation)",
            "system_prompt": system_prompt,
        }
        answer: str = self._invoke_with_retry(invoke_input, session_id)
        _response_time_ms = int((time.time() - _ask_start) * 1000)

        # 6. Persist memory
        self.memory.add_message(session_id, "user", question)
        self.memory.add_message(session_id, "assistant", answer)

        # 6b. Log fallback if the bot couldn't answer
        is_fallback = looks_like_fallback(answer)
        if is_fallback:
            from chatbot.core.fallback_log import FallbackEntry
            self.fallback_log.log(FallbackEntry(
                question=question,
                answer_given=answer,
                session_id=session_id,
                language=language or "",
            ))

        # 6c. Track analytics
        if self.analytics:
            channel = _channel_from_session(session_id)
            self.analytics.track_question(
                session_id=session_id,
                question=question,
                response_time_ms=_response_time_ms,
                language=language or "",
                channel=channel,
                was_fallback=is_fallback,
                personality=active_profile.personality.name,
                ab_variant=ab_variant_name,
            )

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
