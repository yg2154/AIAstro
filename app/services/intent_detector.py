import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Keyword → category mapping (lower-cased)
_KEYWORD_MAP = {
    "career": [
        "career", "job", "work", "profession", "vocation", "business",
        "employment", "occupation", "salary", "promotion", "success",
        "entrepreneurship", "startup", "money", "wealth", "finance",
        "income", "earning", "professional", "office",
    ],
    "love": [
        "love", "relationship", "marriage", "partner", "romantic", "romance",
        "soulmate", "compatibility", "dating", "husband", "wife", "spouse",
        "attraction", "breakup", "divorce", "wedding", "heart",
    ],
    "spiritual": [
        "spiritual", "spirituality", "karma", "dharma", "moksha", "meditation",
        "yoga", "mantra", "chakra", "soul", "enlightenment", "liberation",
        "past life", "rebirth", "god", "goddess", "worship", "ritual",
        "vedic", "upanishad", "vedanta", "puja", "temple", "prayer",
    ],
    "planetary": [
        "planet", "saturn", "jupiter", "mars", "venus", "mercury",
        "sun", "moon", "rahu", "ketu", "transit", "mahadasha",
        "dasha", "retrograde", "shani", "mangal", "surya", "chandra",
        "shukra", "budha", "guru", "sade sati",
    ],
    "nakshatra": [
        "nakshatra", "star", "lunar mansion", "ashwini", "bharani",
        "krittika", "rohini", "mrigashira", "ardra", "punarvasu",
        "pushya", "ashlesha", "magha", "phalguni", "hasta", "chitra",
        "swati", "vishakha", "anuradha", "jyeshtha", "mula", "ashadha",
        "shravana", "dhanishtha", "shatabhisha", "bhadrapada", "revati",
        "birth star",
    ],
    "chitchat": [
        "hello", "hi", "hey", "how are you", "what is your name",
        "who are you", "good morning", "good evening", "thanks",
        "thank you", "bye", "goodbye", "help", "what can you do",
    ],
}

# Intents that should trigger retrieval
RETRIEVAL_INTENTS = {"career", "love", "spiritual", "planetary", "nakshatra"}


def detect_intent(message: str) -> Tuple[str, float]:
    """
    Return (intent_category, confidence) via keyword matching.
    Falls back to 'chitchat' with low confidence.
    """
    msg_lower = message.lower()

    scores: dict[str, int] = {}
    for category, keywords in _KEYWORD_MAP.items():
        count = sum(1 for kw in keywords if kw in msg_lower)
        if count:
            scores[category] = count

    if not scores:
        return "chitchat", 0.4

    best = max(scores, key=lambda c: scores[c])
    # Normalize to [0.7, 0.95]
    confidence = min(0.7 + scores[best] * 0.05, 0.95)
    return best, confidence


async def detect_intent_with_llm_fallback(message: str, openai_api_key: str = None) -> Tuple[str, float]:
    """
    Two-pass intent detection.
    Pass 1: keyword lookup (always free).
    Pass 2: tiny LLM call if message long + low confidence + key available.
    """
    intent, confidence = detect_intent(message)
    word_count = len(message.split())

    if word_count > 12 and confidence < 0.85 and openai_api_key:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_api_key)
            system = (
                "You are a Vedic astrology classifier. Classify the user message into exactly one of: "
                "career, love, spiritual, planetary, nakshatra, chitchat. Reply with only the category word."
            )
            resp = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": system}, {"role": "user", "content": message}],
                max_tokens=5,
                temperature=0,
            )
            llm_intent = resp.choices[0].message.content.strip().lower()
            if llm_intent in _KEYWORD_MAP:
                logger.debug("LLM intent override: %s → %s", intent, llm_intent)
                return llm_intent, 0.90
        except Exception as exc:
            logger.warning("LLM intent fallback failed: %s", exc)

    return intent, confidence
