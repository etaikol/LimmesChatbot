"""
LangChain Expression Language (LCEL) chains.

``build_rag_chain`` returns a runnable that takes:

    {"question": str, "history": str, "system_prompt": str}

and returns the assistant's answer as a string.

It internally:

1. Runs the retriever on ``question`` and formats results into ``context``.
2. Fills the chat template with ``system_prompt`` + history + context + question.
3. Calls the LLM and parses to a plain string.

Why ``system_prompt`` is an *input* and not baked in:
    The engine wants to swap the system prompt per request — so the user
    can pick their language in the widget without rebuilding the chain.
    The engine passes a default if the caller doesn't specify one.
"""

from __future__ import annotations

from typing import Any

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable, RunnableLambda

from chatbot.core.prompts import RAG_CHAT_TEMPLATE, REWRITE_TEMPLATE


def _format_docs(docs: list[Document]) -> str:
    if not docs:
        return "(no relevant context found)"
    blocks: list[str] = []
    for d in docs:
        meta = d.metadata or {}
        src = meta.get("source") or meta.get("file_name") or "unknown"
        page = meta.get("page")
        head = f"[{src}{f' p.{page}' if page is not None else ''}]"
        blocks.append(f"{head}\n{d.page_content}")
    return "\n\n---\n\n".join(blocks)


def build_rag_chain(
    llm: BaseChatModel,
    retriever: BaseRetriever,
    system_prompt: str,
) -> Runnable:
    """Build a RAG runnable.

    Inputs at call time (``chain.invoke(...)``):

    - ``question`` (str, required)
    - ``history``  (str, optional)
    - ``system_prompt`` (str, optional — falls back to the value passed
      to ``build_rag_chain`` so existing call sites do not break)
    """

    default_system_prompt = system_prompt

    # Rewrite chain: turns multi-turn follow-ups into standalone queries
    rewrite_chain = REWRITE_TEMPLATE | llm | StrOutputParser()

    def _maybe_rewrite(inputs: dict[str, Any]) -> str:
        """Rewrite the question when there is conversation history."""
        question = inputs.get("question", "")
        history = inputs.get("history") or ""
        if not history or history == "(no prior conversation)" or history == "(none)":
            return question
        try:
            return rewrite_chain.invoke({"question": question, "history": history})
        except Exception:
            return question  # fall back to original on any error

    def fetch_context(inputs: dict[str, Any]) -> str:
        question = inputs.get("_search_query") or inputs.get("question", "")
        docs = retriever.invoke(question)
        return _format_docs(docs)

    chain = (
        # First: optionally rewrite the question for better retrieval
        RunnableLambda(lambda x: {**x, "_search_query": _maybe_rewrite(x)})
        | {
            "system_prompt": RunnableLambda(
                lambda x: x.get("system_prompt") or default_system_prompt
            ),
            "context": RunnableLambda(fetch_context),
            "history": RunnableLambda(lambda x: x.get("history") or "(none)"),
            "question": RunnableLambda(lambda x: x["question"]),
        }
        | RAG_CHAT_TEMPLATE
        | llm
        | StrOutputParser()
    )
    return chain
