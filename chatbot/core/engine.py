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

from typing import Any, Optional

from pydantic import BaseModel, Field

from chatbot.core.memory import SessionStore
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
from chatbot.settings import Settings, get_settings


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
        3. Estimate input tokens and check the daily budget guard
           (cheap, blocks before any paid call).
        4. Run the LangChain RAG chain (paid).
        5. Persist memory + collect sources for citation.
        6. Record actual token usage in the budget guard.
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

        logger.debug("[{}] User: {}", session_id, question)

        history = self.memory.history_text(session_id)

        # 3. Budget pre-check (estimate is intentionally pessimistic).
        est_in = estimate_tokens(question + (history or ""))
        try:
            self.budget.check_can_spend(est_in)
        except BudgetExceeded as exc:
            logger.warning("[{}] Budget exceeded: {}", session_id, exc.reason)
            raise BudgetError(exc.reason) from exc

        # 4. The actual paid LLM call. Build the system prompt now so we
        #    can honor a per-request language without rebuilding the chain.
        system_prompt = self.profile.build_system_prompt(language=language)
        try:
            answer: str = self.chain.invoke(
                {
                    "question": question,
                    "history": history or "(no prior conversation)",
                    "system_prompt": system_prompt,
                }
            )
        except ChatbotError:
            raise
        except Exception as exc:  # pragma: no cover - provider failures
            friendly = explain_llm_error(exc)
            logger.exception("[{}] LLM call failed: {}", session_id, exc)
            raise LLMError(friendly, user_message=friendly) from exc

        # 5. Persist memory
        self.memory.add_message(session_id, "user", question)
        self.memory.add_message(session_id, "assistant", answer)

        sources = self._collect_sources(question)

        # 6. Record actual usage. We re-estimate from the strings because
        # not all providers expose .usage_metadata uniformly.
        try:
            self.budget.record(
                input_tokens=est_in,
                output_tokens=estimate_tokens(answer),
            )
        except Exception as exc:  # never let metering crash a reply
            logger.warning("[{}] budget.record failed: {}", session_id, exc)

        logger.debug(
            "[{}] Bot: {}{}",
            session_id,
            answer[:120],
            "..." if len(answer) > 120 else "",
        )

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            sources=sources,
        )

    def greet(self) -> str:
        return self.profile.greeting

    def reset(self, session_id: str) -> None:
        """Forget a single conversation."""
        session_id = sanitize_session_id(session_id)
        self.memory.clear(session_id)
        logger.info("Cleared session: {}", session_id)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _collect_sources(self, question: str) -> list[SourceDocument]:
        try:
            docs = self.retriever.retrieve(question)
        except Exception as e:
            logger.warning("Failed to collect sources: {}", e)
            return []

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

    # ── Constructors ────────────────────────────────────────────────────────

    @classmethod
    def from_client(
        cls, client_id: str, settings: Optional[Settings] = None
    ) -> Chatbot:
        """Build a Chatbot from a YAML client config under `config/clients/`."""
        profile = ChatbotProfile.load(client_id)
        return cls(profile=profile, settings=settings)

    @classmethod
    def from_env(cls) -> Chatbot:
        """Build a Chatbot using `settings.active_client` (default: 'default')."""
        s = get_settings()
        return cls.from_client(s.active_client, settings=s)
