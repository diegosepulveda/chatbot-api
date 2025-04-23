from fastapi import APIRouter, Response, Cookie, HTTPException
from typing import Optional
from app.services.chat_session_manager import ChatSessionManager
from app.services.prompt_security_barrier import PromptSecurityBarrier
from app.services.llm_client import LLMClient
from app.services.query_parameters import QueryParameters
from app.models.schemas import ChatRequest, ChatResponse, HistoryResponse
from app.config.redis import redis_instance
import logging
import traceback

logger = logging.getLogger(__name__)
router = APIRouter()

sessions = ChatSessionManager(redis_instance=redis_instance)
guard = PromptSecurityBarrier()
llm = LLMClient()


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    res: Response,
    session_id: Optional[str] = Cookie(default=None)
):
    try:
        sid = sessions.get_or_create(session_id)
        res.set_cookie("session_id", sid, httponly=True, samesite="lax")

        sanitized = PromptSecurityBarrier.sanitize(req.message)
        sessions.add_message(sid, "user", sanitized)

        answer = llm.query(sessions.as_prompt(sid))

        url = None
        if (params := QueryParameters.from_llm_text(answer)) and params.is_complete():
            sessions.record_query(sid, params)
            url = params.to_query_url()

        sessions.add_message(sid, "assistant", answer)

        return {"response": answer, "session_id": sid, "url": url}

    except Exception:
        print("Error in chat endpoint")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error while processing the chat.")


@router.get("/api/v1/history", response_model=HistoryResponse)
def history(
    res: Response,
    session_id: Optional[str] = Cookie(default=None)
):
    try:
        sid = sessions.get_or_create(session_id)
        res.set_cookie("session_id", sid, httponly=True, samesite="lax")

        history = sessions._load(sid)
        return {"history": history}
    except Exception:
        logger.exception("Failed to retrieve history")
        raise HTTPException(status_code=500, detail="Internal server error while fetching chat history.")
