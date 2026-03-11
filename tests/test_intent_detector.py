import pytest
from app.services.intent_detector import detect_intent, RETRIEVAL_INTENTS


class TestDetectIntent:
    def test_career_keyword(self):
        intent, confidence = detect_intent("What career suits me?")
        assert intent == "career"
        assert confidence >= 0.7

    def test_love_keyword(self):
        intent, confidence = detect_intent("When will I find love?")
        assert intent == "love"

    def test_spiritual_keyword(self):
        intent, confidence = detect_intent("What is my karma?")
        assert intent == "spiritual"

    def test_planetary_keyword(self):
        intent, confidence = detect_intent("How does Saturn transit affect me?")
        assert intent == "planetary"

    def test_nakshatra_keyword(self):
        intent, confidence = detect_intent("What is my nakshatra?")
        assert intent == "nakshatra"

    def test_chitchat_keyword(self):
        intent, confidence = detect_intent("Hello, how are you?")
        assert intent == "chitchat"

    def test_chitchat_not_in_retrieval_intents(self):
        assert "chitchat" not in RETRIEVAL_INTENTS

    def test_retrieval_intents_present(self):
        for expected in ("career", "love", "spiritual", "planetary", "nakshatra"):
            assert expected in RETRIEVAL_INTENTS

    def test_unknown_message_returns_chitchat(self):
        intent, confidence = detect_intent("blahblahblah xyz")
        assert intent == "chitchat"

    def test_multiple_keywords_boost_confidence(self):
        _, c1 = detect_intent("career")
        _, c2 = detect_intent("career job work profession")
        assert c2 >= c1
