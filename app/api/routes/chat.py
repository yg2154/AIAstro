import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.intent_detector import detect_intent_with_llm_fallback, RETRIEVAL_INTENTS
from app.services.language_handler import build_system_prompt
from app.services.llm_client import get_llm_client
from app.services.rag_engine import get_rag_engine
from app.services.session_manager import get_session_manager
from app.services.zodiac_calculator import get_zodiac_sign, get_nakshatra
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    session_mgr = get_session_manager()
    session = session_mgr.get_or_create(request.session_id)

    # --- Resolve user profile (use cached if not provided) ---
    profile = request.user_profile
    if profile is not None:
        # New or updated profile: compute zodiac + nakshatra
        try:
            zodiac = get_zodiac_sign(profile.birth_date)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        nakshatra = get_nakshatra(profile.birth_date, profile.birth_time, profile.birth_place)
        session_mgr.update_profile(
            request.session_id,
            profile.model_dump(),
            zodiac,
            nakshatra,
        )
    else:
        # Fall back to session-cached profile
        zodiac = session.zodiac
        nakshatra = session.nakshatra
        if session.user_profile:
            from app.models.schemas import UserProfile
            profile = UserProfile(**session.user_profile)

    language = profile.preferred_language if profile else "en"
    user_name = profile.name if profile else None

    # --- Intent detection ---
    intent, confidence = await detect_intent_with_llm_fallback(
        request.message, openai_api_key=settings.openai_api_key
    )
    logger.debug("Intent: %s (confidence=%.2f)", intent, confidence)

    # --- RAG retrieval ---
    context_chunks: List[str] = []
    retrieval_used = False

    if intent in RETRIEVAL_INTENTS:
        rag = get_rag_engine()
        if rag.is_ready:
            context_chunks, retrieval_used = rag.retrieve(
                query=request.message,
                zodiac=zodiac,
            )

    # --- Build conversation messages ---
    system_prompt = build_system_prompt(
        zodiac=zodiac,
        nakshatra=nakshatra,
        user_name=user_name,
        intent=intent,
        context_chunks=context_chunks,
        language=language,
    )

    history = session.get_history()
    messages = [{"role": "system", "content": system_prompt}] + history + [
        {"role": "user", "content": request.message}
    ]

    # --- LLM call ---
    llm = get_llm_client()
    try:
        answer = await llm.complete(messages)
    except Exception as exc:
        logger.error("LLM error: %s", exc)
        raise HTTPException(status_code=502, detail="LLM service unavailable. Please try again.")

    # --- Update session history ---
    session.add_turn("user", request.message)
    session.add_turn("assistant", answer)

    return ChatResponse(
        response=answer,
        zodiac=zodiac,
        context_used=context_chunks,
        retrieval_used=retrieval_used,
    )
