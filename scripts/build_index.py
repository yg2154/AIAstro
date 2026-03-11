#!/usr/bin/env python3
"""Manual FAISS index rebuild utility."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.rag_engine import get_rag_engine
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

if __name__ == "__main__":
    print("Building FAISS index from knowledge base...")
    rag = get_rag_engine()
    rag.build_index()
    print(f"Done. Index contains {rag._index.ntotal} vectors across {len(rag._chunks)} chunks.")
