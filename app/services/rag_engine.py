import json
import logging
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent.parent / "knowledge_base"


class RAGEngine:
    def __init__(self, similarity_threshold: float = 0.35, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.similarity_threshold = similarity_threshold
        self.embedding_model_name = embedding_model
        self._model = None
        self._index = None
        self._chunks: List[str] = []
        self._chunk_metadata: List[dict] = []

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.embedding_model_name)
        return self._model

    def build_index(self) -> None:
        """Load knowledge base files, chunk them, encode, and build FAISS index."""
        import faiss

        chunks, metadata = self._load_all_documents()
        self._chunks = chunks
        self._chunk_metadata = metadata

        logger.info("Encoding %d chunks with %s", len(chunks), self.embedding_model_name)
        model = self._get_model()
        embeddings = model.encode(chunks, show_progress_bar=False, convert_to_numpy=True)

        # L2-normalize for cosine similarity via inner product
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        embeddings = (embeddings / norms).astype(np.float32)

        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings)
        logger.info("FAISS index built with %d vectors (dim=%d)", self._index.ntotal, dim)

    def retrieve(self, query: str, zodiac: str = None, top_k: int = 5) -> Tuple[List[str], bool]:
        """Return (relevant_chunks, retrieval_used)."""
        if self._index is None or len(self._chunks) == 0:
            return [], False

        model = self._get_model()
        query_emb = model.encode([query], show_progress_bar=False, convert_to_numpy=True)
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm
        query_emb = query_emb.astype(np.float32)

        k = min(top_k * 2, self._index.ntotal)
        scores, indices = self._index.search(query_emb, k)

        scores = scores[0]
        indices = indices[0]

        if len(scores) == 0 or scores[0] < self.similarity_threshold:
            return [], False

        # Zodiac boost: +0.1 to chunks mentioning the zodiac sign
        boosted = []
        for score, idx in zip(scores, indices):
            if idx < 0:
                continue
            chunk_score = float(score)
            if zodiac and zodiac.lower() in self._chunks[idx].lower():
                chunk_score += 0.1
            boosted.append((chunk_score, idx))

        boosted.sort(key=lambda x: x[0], reverse=True)
        top = boosted[:top_k]

        result_chunks = [self._chunks[idx] for _, idx in top if float(_) >= self.similarity_threshold]
        if not result_chunks:
            return [], False

        return result_chunks, True

    @property
    def is_ready(self) -> bool:
        return self._index is not None and self._index.ntotal > 0

    # ---- Document loading & chunking ----------------------------------------

    def _load_all_documents(self) -> Tuple[List[str], List[dict]]:
        chunks: List[str] = []
        metadata: List[dict] = []

        files = [
            ("zodiac_traits.json", self._chunk_json_zodiac),
            ("planetary_impacts.json", self._chunk_json_planetary),
            ("nakshatra_mapping.json", self._chunk_json_nakshatra),
            ("career_guidance.txt", self._chunk_txt),
            ("love_guidance.txt", self._chunk_txt),
            ("spiritual_guidance.txt", self._chunk_txt),
        ]

        for filename, chunker in files:
            path = KNOWLEDGE_BASE_DIR / filename
            if not path.exists():
                logger.warning("Knowledge base file not found: %s", path)
                continue
            try:
                new_chunks, new_meta = chunker(path)
                chunks.extend(new_chunks)
                metadata.extend(new_meta)
                logger.debug("Loaded %d chunks from %s", len(new_chunks), filename)
            except Exception as exc:
                logger.error("Failed to load %s: %s", filename, exc)

        return chunks, metadata

    def _chunk_json_zodiac(self, path: Path) -> Tuple[List[str], List[dict]]:
        with open(path) as f:
            data = json.load(f)
        chunks, meta = [], []
        for sign, info in data.items():
            for key in ["strengths", "weaknesses", "career", "love", "spiritual"]:
                if key in info:
                    text = f"{sign} - {key.capitalize()}: {info[key]}"
                    if "traits" in info:
                        text = f"{sign} ({', '.join(info['traits'])}) - {key.capitalize()}: {info[key]}"
                    chunks.append(text)
                    meta.append({"source": "zodiac_traits.json", "sign": sign, "category": key})
        return chunks, meta

    def _chunk_json_planetary(self, path: Path) -> Tuple[List[str], List[dict]]:
        with open(path) as f:
            data = json.load(f)
        chunks, meta = [], []
        for planet, info in data.items():
            for key in ["career_guidance", "spiritual_guidance", "positive_transit", "challenging_transit"]:
                if key in info:
                    text = f"{planet} ({info.get('Sanskrit', planet)}) - {key.replace('_', ' ').title()}: {info[key]}"
                    chunks.append(text)
                    meta.append({"source": "planetary_impacts.json", "planet": planet, "category": key})
        return chunks, meta

    def _chunk_json_nakshatra(self, path: Path) -> Tuple[List[str], List[dict]]:
        with open(path) as f:
            data = json.load(f)
        chunks, meta = [], []
        for n in data.get("nakshatras", []):
            name = n.get("name", "")
            text = (
                f"Nakshatra {name} (ruled by {n.get('ruling_planet', '')}, zodiac {n.get('zodiac', '')}): "
                f"Qualities: {', '.join(n.get('qualities', []))}. "
                f"Career: {n.get('career', '')}. "
                f"Spiritual: {n.get('spiritual', '')}"
            )
            chunks.append(text)
            meta.append({"source": "nakshatra_mapping.json", "nakshatra": name})
        return chunks, meta

    def _chunk_txt(self, path: Path) -> Tuple[List[str], List[dict]]:
        with open(path) as f:
            content = f.read()
        # Split on double newlines, keep chunks ≥50 chars
        raw_chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) >= 50]
        meta = [{"source": path.name}] * len(raw_chunks)
        return raw_chunks, meta


# Module-level singleton
_rag_engine: RAGEngine = None


def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        from app.core.config import get_settings
        settings = get_settings()
        _rag_engine = RAGEngine(
            similarity_threshold=settings.rag_similarity_threshold,
            embedding_model=settings.embedding_model,
        )
    return _rag_engine
