from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class UserProfile(BaseModel):
    name: str
    birth_date: str  # YYYY-MM-DD
    birth_time: Optional[str] = None  # HH:MM
    birth_place: Optional[str] = None
    preferred_language: str = "en"  # "en" or "hi"


class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    user_profile: Optional[UserProfile] = None


class ChatResponse(BaseModel):
    response: str
    zodiac: Optional[str] = None
    context_used: List[str] = Field(default_factory=list)
    retrieval_used: bool = False
