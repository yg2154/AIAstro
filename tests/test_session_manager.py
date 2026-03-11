import asyncio
from datetime import datetime, timedelta
import pytest
from app.services.session_manager import SessionManager, Session


class TestSessionManager:
    def setup_method(self):
        self.mgr = SessionManager(ttl_minutes=60)

    def test_get_or_create_new_session(self):
        session = self.mgr.get_or_create("abc")
        assert isinstance(session, Session)
        assert session.session_id == "abc"

    def test_get_or_create_same_session(self):
        s1 = self.mgr.get_or_create("abc")
        s2 = self.mgr.get_or_create("abc")
        assert s1 is s2

    def test_get_nonexistent_returns_none(self):
        assert self.mgr.get("nonexistent") is None

    def test_add_turns_preserved(self):
        session = self.mgr.get_or_create("s1")
        session.add_turn("user", "Hello")
        session.add_turn("assistant", "Hi!")
        history = session.get_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_sliding_window_eviction(self):
        session = self.mgr.get_or_create("s2")
        for i in range(15):
            session.add_turn("user", f"msg{i}")
        # maxlen=10 → only last 10 turns kept
        assert len(session.turns) == 10
        assert list(session.turns)[-1].content == "msg14"

    def test_update_profile(self):
        self.mgr.update_profile("s3", {"name": "Priya"}, "Scorpio", "Anuradha")
        session = self.mgr.get("s3")
        assert session.zodiac == "Scorpio"
        assert session.nakshatra == "Anuradha"
        assert session.user_profile == {"name": "Priya"}

    def test_ttl_eviction(self):
        mgr = SessionManager(ttl_minutes=1)
        session = mgr.get_or_create("old")
        # Force last_active to be expired
        session.last_active = datetime.utcnow() - timedelta(minutes=2)
        mgr._evict_expired()
        assert mgr.get("old") is None

    def test_active_session_not_evicted(self):
        mgr = SessionManager(ttl_minutes=60)
        mgr.get_or_create("active")
        mgr._evict_expired()
        assert mgr.get("active") is not None
