"""
Prompt templates used by the engine.

Kept in their own module so personality designers and prompt engineers have
one obvious place to tune wording without touching glue code.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

# Main RAG chat template. The personality's `system_prompt` is injected as
# `{system_prompt}`. Conversation history and retrieved context follow.
RAG_CHAT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", "{system_prompt}"),
        (
            "system",
            (
                "Use the following knowledge-base context when answering. "
                "If the answer is not contained in the context, say so honestly "
                "and offer to escalate to a human if appropriate. Do NOT invent "
                "facts about the business.\n\n"
                "=== Context ===\n{context}\n=== End Context ==="
            ),
        ),
        ("system", "Recent conversation:\n{history}"),
        (
            "system",
            (
                "Reminder: reply in the SAME language the user is writing in. "
                "If the user writes in Thai, reply in Thai. If in Russian, reply in Russian. "
                "The context above may be in a different language — translate your answer, "
                "do not copy it verbatim."
            ),
        ),
        ("human", "{question}"),
    ]
)


# Used by the optional translation tool
TRANSLATE_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a professional translator. Translate the following text "
                "into {target_language}. Preserve formatting, tone, and meaning. "
                "Do not add commentary."
            ),
        ),
        ("human", "{text}"),
    ]
)


# Standalone-question rewriting template — used to turn a follow-up question
# into a self-contained query for retrieval. Improves recall of the vector DB.
REWRITE_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "Given a conversation history and a follow-up question, rephrase "
                "the question to be a standalone search query. Output only the "
                "rewritten question — nothing else."
            ),
        ),
        ("human", "History:\n{history}\n\nFollow-up: {question}"),
    ]
)
