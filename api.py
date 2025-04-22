from fastapi import FastAPI, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
from core import ChatSessionManager, PromptSecurityBarrier, LLMClient
import os, uuid, requests, redis, json

# Load env vars
load_dotenv()

# -------------------------------------------------
# FastAPI instance & CORS
# -------------------------------------------------
app = FastAPI(title="Real‑Estate Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # or ["https://your‑site.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Singletons
# -------------------------------------------------
sessions = ChatSessionManager()
guard = PromptSecurityBarrier()
llm = LLMClient()

# -------------------------------------------------
# Schemas
# -------------------------------------------------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    session_id: str


class HistoryResponse(BaseModel):
    history: list[dict]


# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    res: Response,
    session_id: Optional[str] = Cookie(default=None),
):
    session_id = sessions.get_or_create(session_id)
    res.set_cookie("session_id", session_id, httponly=True, samesite="lax")

    if not guard.is_valid(req.message):
        return {"response": "Sorry, your prompt was blocked.", "session_id": session_id}

    sessions.add(session_id, "user", req.message)
    answer = llm.query(sessions.as_prompt(session_id))
    sessions.add(session_id, "assistant", answer)

    return {"response": answer, "session_id": session_id}


@app.get("/history", response_model=HistoryResponse)
def history(session_id: Optional[str] = Cookie(default=None)):
    if not session_id or not sessions._load(session_id):
        return {"history": []}
    return {"history": sessions._load(session_id)}


@app.get("/")
def root():
    return {"status": "ok"}