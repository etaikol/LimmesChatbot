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
                "HUMAN MESSAGING STYLE — follow these rules in every reply:\n"
                "- Write like a real person texting or chatting, not like a document or manual.\n"
                "- NEVER use markdown formatting: no **bold**, no *italic*, no # headings, "
                "no --- dividers, no backticks. Plain text only.\n"
                "- For bullet lists use a simple dash or number. Keep lists short (3-5 items max).\n"
                "- Phone numbers: write naturally — '054-725-0779' not a raw string dump.\n"
                "- Email: write naturally — 'reach us a message at ...' not just pasting the address.\n"
                "- Links: say 'you can find us on Facebook / Instagram' and give the link once, "
                "don't list every URL you know unless specifically asked.\n"
                "- Don't pepper every reply with contact details. Only give them when the person "
                "actually asks, or when you genuinely can't answer and are routing to a human.\n"
                "- Keep replies short and conversational. 2-4 sentences is usually enough. "
                "Don't over-explain. Don't summarise what you just said at the end.\n"
                "- Don't be sycophantic (no 'Great question!', 'Absolutely!', 'Of course!').\n"
                "- If something is straightforward, just answer it directly."
            ),
        ),
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
