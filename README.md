# MyNaksh — Vedic Astrology Conversational AI

A production-ready RAG + multi-turn conversational AI service for Vedic astrology. Users provide birth details and ask multi-turn questions; the system responds with personalized, knowledge-grounded answers using intent-aware retrieval.

## Live Demo

> **Public URL:** *(Add Render URL after deployment)*

### Quick Test (cURL)

```bash
curl -X POST https://<your-render-url>/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What career paths suit me?",
    "user_profile": {
      "name": "Priya",
      "birth_date": "1992-11-15",
      "birth_time": "14:30",
      "birth_place": "Mumbai",
      "preferred_language": "en"
    }
  }'
```

**Multi-turn (second request — no profile needed):**
```bash
curl -X POST https://<your-render-url>/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What about love and relationships?"
  }'
```

**Hindi response:**
```bash
curl -X POST https://<your-render-url>/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440001",
    "message": "मेरे करियर के बारे में बताएं",
    "user_profile": {
      "name": "Ravi",
      "birth_date": "1995-08-10",
      "preferred_language": "hi"
    }
  }'
```

---

## Architecture

```
User Request
    │
    ▼
POST /api/v1/chat
    │
    ├── Session Manager (in-memory, deque(maxlen=10) sliding window)
    │       └── Cached user profile + zodiac across turns
    │
    ├── Zodiac Calculator (date-range lookup + ephem nakshatra)
    │
    ├── Intent Detector (keyword dict → optional LLM refinement)
    │       └── career | love | spiritual | planetary | nakshatra | chitchat
    │
    ├── RAG Engine (FAISS IndexFlatIP + all-MiniLM-L6-v2)
    │       └── Only fires for non-chitchat intents
    │       └── Zodiac boost: +0.1 for sign-matched chunks
    │       └── Threshold gate: similarity < 0.35 → skip retrieval
    │
    ├── Language Handler (build_system_prompt with RAG context)
    │
    └── LLM Client
            ├── OpenAIClient (gpt-3.5-turbo, 1 retry)
            └── StubLLMClient (all 12 signs × 5 intents, EN + HI)
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vector store | FAISS IndexFlatIP | CPU-only, zero infra cost, exact cosine search |
| Embedding model | all-MiniLM-L6-v2 | 22MB, free, multilingual-capable |
| Session memory | deque(maxlen=10) | Bounded O(1) sliding window, no external state |
| LLM fallback | StubLLMClient | Public demo works without API key |
| Intent detection | Keywords + optional LLM | Free first-pass, LLM refines only when needed |
| Language | System prompt directive | No post-hoc translation; set at generation time |

---

## API Reference

### `POST /api/v1/chat`

**Request:**
```json
{
  "session_id": "uuid4-string",
  "message": "What career suits me?",
  "user_profile": {
    "name": "string",
    "birth_date": "YYYY-MM-DD",
    "birth_time": "HH:MM",
    "birth_place": "string",
    "preferred_language": "en"
  }
}
```

**Response:**
```json
{
  "response": "As a Scorpio with strong Mars influence...",
  "zodiac": "Scorpio",
  "context_used": ["Scorpio - Career: ..."],
  "retrieval_used": true
}
```

`user_profile` is optional after the first request in a session — the profile is cached.

### `GET /health`
```json
{"status": "ok", "rag_ready": true}
```

---

## Local Development

```bash
# 1. Clone and set up environment
git clone https://github.com/<your-username>/MyNaksh.git
cd MyNaksh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 2. Configure environment
cp .env.example .env
# Edit .env — OPENAI_API_KEY is optional

# 3. Run the server
uvicorn app.main:app --reload

# 4. Run tests (no API key needed)
pytest tests/ -v

# 5. Run evaluation
python scripts/evaluate.py
```

### Docker

```bash
docker build -t mynaksh .
docker run -p 8000:8000 mynaksh

# Health check
curl http://localhost:8000/health
```

---

## Deployment (Render.com)

1. Push to a public GitHub repository.
2. Go to [Render.com](https://render.com) → **New Web Service** → connect your GitHub repo.
3. Select **Docker** as the runtime (Render detects `Dockerfile` automatically).
4. Set `OPENAI_API_KEY` as a secret environment variable in Render dashboard (optional).
5. Deploy — `render.yaml` in the repo root configures the rest.

The Docker image pre-downloads the `all-MiniLM-L6-v2` model at build time, preventing cold-start delays on Render's free tier.

---

## Knowledge Base

| File | Contents |
|------|----------|
| `zodiac_traits.json` | All 12 signs: traits, career, love, spiritual, compatibility |
| `planetary_impacts.json` | 9 planets: career guidance, spiritual practices, transits |
| `nakshatra_mapping.json` | All 27 nakshatras: deity, planet, qualities, career, spiritual |
| `career_guidance.txt` | Vedic astrology career principles by element, planet, Mahadasha |
| `love_guidance.txt` | Relationship guidance: Venus placements, 7th house, compatibility |
| `spiritual_guidance.txt` | Dharma, karma, moksha, planetary remedies, spiritual practices |

---

## Testing

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

Tests run entirely with `StubLLMClient` — no OpenAI API key required.

| Test File | Coverage |
|-----------|----------|
| `test_chat_endpoint.py` | Integration: full request cycle, session memory, Hindi, invalid inputs |
| `test_zodiac_calculator.py` | All 12 sign boundaries + edge cases |
| `test_intent_detector.py` | Keyword categories, confidence scoring, retrieval intent set |
| `test_rag_engine.py` | Retrieval relevance, threshold gate, zodiac boost |
| `test_session_manager.py` | Window eviction, TTL expiry, profile caching |

---

## RAG Evaluation

```bash
python scripts/evaluate.py
```

Demonstrates two cases:
- **Case 1 (retrieval helps):** Career query for Scorpio retrieves relevant planetary/zodiac knowledge, enriching the response.
- **Case 2 (retrieval hurts):** Simple greeting forced through RAG receives irrelevant astrological content; proper intent detection prevents this.
