import json
import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent.parent / "knowledge_base"


class RAGEngine:
    def __init__(self, similarity_threshold: float = 0.35, embedding_model: str = ""):
        self.similarity_threshold = similarity_threshold
        self._vectorizer = None
        self._tfidf_matrix = None
        self._chunks: List[str] = []
        self._chunk_metadata: List[dict] = []

    def build_index(self) -> None:
        """Load knowledge base files, chunk them, and build TF-IDF index."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        chunks, metadata = self._load_all_documents()
        self._chunks = chunks
        self._chunk_metadata = metadata

        logger.info("Building TF-IDF index over %d chunks", len(chunks))
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=8000,
            sublinear_tf=True,
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(chunks)
        logger.info("TF-IDF index built (%d chunks, %d features)", len(chunks), self._tfidf_matrix.shape[1])

    def retrieve(self, query: str, zodiac: str = None, top_k: int = 5) -> Tuple[List[str], bool]:
        """Return (relevant_chunks, retrieval_used)."""
        if self._tfidf_matrix is None or len(self._chunks) == 0:
            return [], False

        from sklearn.metrics.pairwise import cosine_similarity

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix)[0]

        if scores.max() < self.similarity_threshold:
            return [], False

        # Zodiac boost: +0.1 to chunks mentioning the zodiac sign
        if zodiac:
            for i, chunk in enumerate(self._chunks):
                if zodiac.lower() in chunk.lower():
                    scores[i] += 0.1

        top_indices = scores.argsort()[::-1][:top_k]
        result_chunks = [
            self._chunks[i] for i in top_indices
            if scores[i] >= self.similarity_threshold
        ]

        if not result_chunks:
            return [], False

        return result_chunks, True

    @property
    def is_ready(self) -> bool:
        return self._tfidf_matrix is not None and len(self._chunks) > 0

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
        )
    return _rag_engine
