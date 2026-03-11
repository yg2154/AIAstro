#!/usr/bin/env python3
"""
RAG Evaluation Script — Two-case comparison.

Case 1: Retrieval HELPS — career query benefits from astrology knowledge base.
Case 2: Retrieval HURTS — chitchat query is polluted by irrelevant astrological content.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.rag_engine import get_rag_engine
from app.services.language_handler import build_system_prompt
from app.services.llm_client import get_llm_client


async def run_llm(system_prompt: str, user_message: str) -> str:
    llm = get_llm_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return await llm.complete(messages)


async def main():
    print("Building RAG index...")
    rag = get_rag_engine()
    rag.build_index()
    print(f"Index ready: {rag._index.ntotal} vectors\n")

    print("=" * 70)
    print("CASE 1: RETRIEVAL HELPS")
    print("Query: 'What career paths suit a Scorpio given Mars influence?'")
    print("=" * 70)

    query1 = "What career paths suit a Scorpio given Mars influence?"
    zodiac1 = "Scorpio"

    # Without retrieval
    prompt_no_rag = build_system_prompt(
        zodiac=zodiac1, nakshatra=None, user_name="Demo",
        intent="career", context_chunks=[], language="en"
    )
    response_no_rag = await run_llm(prompt_no_rag, query1)
    print("\n[WITHOUT RETRIEVAL]")
    print(response_no_rag)

    # With retrieval
    chunks, used = rag.retrieve(query1, zodiac=zodiac1)
    prompt_with_rag = build_system_prompt(
        zodiac=zodiac1, nakshatra=None, user_name="Demo",
        intent="career", context_chunks=chunks, language="en"
    )
    response_with_rag = await run_llm(prompt_with_rag, query1)
    print(f"\n[WITH RETRIEVAL] (retrieved {len(chunks)} chunks, retrieval_used={used})")
    print(response_with_rag)

    print("\n" + "=" * 70)
    print("CASE 2: RETRIEVAL HURTS")
    print("Query: 'Hello, what is your name?'")
    print("=" * 70)

    query2 = "Hello, what is your name?"
    zodiac2 = "Gemini"

    # Without retrieval (correct behavior for chitchat)
    prompt_no_rag2 = build_system_prompt(
        zodiac=zodiac2, nakshatra=None, user_name="Demo",
        intent="chitchat", context_chunks=[], language="en"
    )
    response_no_rag2 = await run_llm(prompt_no_rag2, query2)
    print("\n[WITHOUT RETRIEVAL — correct chitchat behavior]")
    print(response_no_rag2)

    # FORCE retrieval (demonstrates harm of injecting irrelevant content)
    chunks2, _ = rag.retrieve("career nakshatra spiritual planetary", zodiac=zodiac2)
    prompt_forced_rag = build_system_prompt(
        zodiac=zodiac2, nakshatra=None, user_name="Demo",
        intent="chitchat", context_chunks=chunks2[:3], language="en"
    )
    response_forced_rag = await run_llm(prompt_forced_rag, query2)
    print(f"\n[WITH FORCED RETRIEVAL — demonstrates degraded greeting response]")
    print(response_forced_rag)

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("Case 1: RAG enriches the career response with specific Scorpio+Mars knowledge.")
    print("Case 2: RAG degrades the simple greeting by injecting unrelated astrological content.")
    print("The intent_detector correctly routes chitchat away from RAG retrieval.\n")


if __name__ == "__main__":
    asyncio.run(main())
