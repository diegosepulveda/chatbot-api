from fastapi import APIRouter, Response, Cookie
from typing import Optional

from app.services.chat_session_manager import ChatSessionManager
from app.services.prompt_security_barrier import PromptSecurityBarrier
from app.services.llm_client import LLMClient
from app.services.query_parameters import QueryParameters
from app.models.schemas import ChatRequest, ChatResponse, HistoryResponse
from app.config.redis import redis_instance

router = APIRouter()
sessions = ChatSessionManager(redis_instance=redis_instance)
guard     = PromptSecurityBarrier()
llm       = LLMClient()


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest,
         res: Response,
         session_id: Optional[str] = Cookie(default=None)):

    sid = sessions.get_or_create(session_id)
    res.set_cookie("session_id", sid, httponly=True, samesite="lax")

    if not guard.is_valid(req.message):
        return {"response": "Sorry, your prompt was blocked.", "session_id": sid}

    sessions.add_message(sid, "user", req.message)
    answer = llm.query(sessions.as_prompt(sid))

    url = None
    if params := QueryParameters.from_llm_text(answer):
        if params.is_complete():
            sessions.record_query(sid, params)
            url = params.to_query_url()

    sessions.add_message(sid, "assistant", answer)
    return {"response": answer, "session_id": sid, "url": url}


@router.get("/api/v1/history", response_model=HistoryResponse)
def history(session_id: Optional[str] = Cookie(default=None)):
    if not session_id:
        return {"history": []}
    return {"history": sessions._load(session_id)}
