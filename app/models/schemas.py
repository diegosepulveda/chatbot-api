
from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    response: str
    session_id: str
    url: Optional[str] = None

class HistoryResponse(BaseModel):
    history: list[dict]