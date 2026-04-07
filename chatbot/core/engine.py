"""
The `Chatbot` class is the single entry point for using the template
programmatically. Channels (CLI, FastAPI, WhatsApp, Telegram, LINE) all
delegate to it.

Lifecycle:
    1. Construct from a `ChatbotProfile` and `Settings`.
    2. On construction, build the LLM, RAG retriever, and LangChain chain.
    3. Each `ask(...)` call retrieves context, runs the chain, persists memory.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from chatbot.core.memory import SessionStore
from chatbot.core.profile import ChatbotProfile
from chatbot.exceptions import ChatbotError, LLMError, explain_llm_error
from chatbot.llm.chains import build_rag_chain
from chatbot.llm.providers import LLMProvider
from chatbot.logging_setup import logger
from chatbot.rag.retriever import RAGRetriever
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
    """High-level orchestrator: profile + memory + RAG + LLM."""

    def __init__(
        self,
        profile: ChatbotProfile,
        settings: Optional[Settings] = None,
        *,
        retriever: Optional[RAGRetriever] = None,
        llm: Optional[LLMProvider] = None,
        memory: Optional[SessionStore] = None,
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

        # Build the LangChain RAG chain once
        self.chain = build_rag_chain(
            llm=self.llm.client,
            retriever=self.retriever.as_langchain_retriever(),
            system_prompt=profile.effective_system_prompt,
        )

        logger.info("Chatbot ready: {}", profile.client.name)

    # ── Public API ──────────────────────────────────────────────────────────

    def ask(self, question: str, session_id: str = "default") -> ChatResponse:
        """Run a single chat turn and return a structured response."""
        question = (question or "").strip()
        if not question:
            return ChatResponse(answer=self.profile.fallback, session_id=session_id)

        logger.debug("[{}] User: {}", session_id, question)

        history = self.memory.history_text(session_id)

        try:
            answer: str = self.chain.invoke(
                {
                    "question": question,
                    "history": history or "(no prior conversation)",
                }
            )
        except ChatbotError:
            raise
        except Exception as exc:  # pragma: no cover - provider failures
            friendly = explain_llm_error(exc)
            logger.exception("[{}] LLM call failed: {}", session_id, exc)
            raise LLMError(friendly, user_message=friendly) from exc

        # Persist memory
        self.memory.add_message(session_id, "user", question)
        self.memory.add_message(session_id, "assistant", answer)

        # Pull source documents for citation
        sources = self._collect_sources(question)

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
