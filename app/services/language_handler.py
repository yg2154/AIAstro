from typing import List, Optional


def build_system_prompt(
    zodiac: Optional[str],
    nakshatra: Optional[str],
    user_name: Optional[str],
    intent: str,
    context_chunks: List[str],
    language: str = "en",
) -> str:
    """Construct the system prompt for the LLM, incorporating RAG context."""
    parts = [
        "You are MyNaksh, a knowledgeable and empathetic Vedic astrology assistant. "
        "You provide personalized, insightful guidance grounded in Jyotish (Vedic astrology) principles. "
        "Be warm, specific, and practically helpful. Avoid generic platitudes.",
    ]

    if user_name:
        parts.append(f"The user's name is {user_name}.")

    if zodiac:
        parts.append(f"The user's Sun sign (zodiac) is {zodiac}.")

    if nakshatra:
        parts.append(f"The user's birth nakshatra is {nakshatra}.")

    if context_chunks:
        parts.append(
            "\n\nRelevant knowledge from the Vedic astrology knowledge base:\n"
            + "\n---\n".join(context_chunks)
        )
        parts.append(
            "\nUse the above knowledge to ground your response. "
            "Integrate it naturally rather than quoting it verbatim."
        )

    parts.append(
        "\nAlways maintain a compassionate, non-fatalistic tone. "
        "Remind the user that astrology reveals tendencies, not fixed destiny."
    )

    if language == "hi":
        parts.append("Respond in Hindi using Devanagari script (हिंदी में देवनागरी लिपि में उत्तर दें).")

    return "\n".join(parts)
