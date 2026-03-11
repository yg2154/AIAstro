import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Turn:
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Session:
    session_id: str
    turns: deque = field(default_factory=lambda: deque(maxlen=10))
    user_profile: Optional[dict] = None
    zodiac: Optional[str] = None
    nakshatra: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append(Turn(role=role, content=content))
        self.last_active = datetime.utcnow()

    def get_history(self) -> List[dict]:
        return [{"role": t.role, "content": t.content} for t in self.turns]


class SessionManager:
    def __init__(self, ttl_minutes: int = 60):
        self._sessions: Dict[str, Session] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._cleanup_task: Optional[asyncio.Task] = None

    def start_cleanup(self) -> None:
        """Start background cleanup task (call from async context)."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    def stop_cleanup(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            self._evict_expired()

    def _evict_expired(self) -> None:
        now = datetime.utcnow()
        expired = [sid for sid, s in self._sessions.items() if now - s.last_active > self._ttl]
        for sid in expired:
            del self._sessions[sid]
            logger.info("Session evicted (TTL): %s", sid)

    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
            logger.debug("Session created: %s", session_id)
        return self._sessions[session_id]

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def update_profile(self, session_id: str, profile: dict, zodiac: str, nakshatra: Optional[str]) -> None:
        session = self.get_or_create(session_id)
        session.user_profile = profile
        session.zodiac = zodiac
        session.nakshatra = nakshatra


# Module-level singleton
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        from app.core.config import get_settings
        settings = get_settings()
        _session_manager = SessionManager(ttl_minutes=settings.session_ttl_minutes)
    return _session_manager
