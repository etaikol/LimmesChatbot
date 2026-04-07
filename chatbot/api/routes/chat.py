"""REST chat endpoint used by the web widget and any custom client."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from chatbot.api.schemas import ChatReply, ChatRequest, ClearReply, SourceModel
from chatbot.exceptions import ChatbotError
from chatbot.logging_setup import logger

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatReply)
async def chat_endpoint(req: ChatRequest, request: Request) -> ChatReply:
    bot = request.app.state.bot
    try:
        resp = bot.ask(req.message, session_id=req.session_id)
    except ChatbotError as e:
        logger.warning("[chat] {}", e)
        raise HTTPException(status_code=502, detail=e.user_message)
    except Exception as e:  # pragma: no cover
        logger.exception("[chat] unexpected: {}", e)
        raise HTTPException(status_code=500, detail="Internal error.")

    return ChatReply(
        answer=resp.answer,
        session_id=resp.session_id,
        sources=[SourceModel(**s.model_dump()) for s in resp.sources],
    )


@router.delete("/chat/{session_id}", response_model=ClearReply)
def clear_session(session_id: str, request: Request) -> ClearReply:
    bot = request.app.state.bot
    bot.reset(session_id)
    return ClearReply(cleared=session_id)
