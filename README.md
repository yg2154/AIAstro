# MyNaksh — Vedic Astrology Conversational AI

A production-ready RAG + multi-turn conversational AI service for Vedic astrology. Users provide birth details and ask multi-turn questions; the system responds with personalized, knowledge-grounded answers using intent-aware retrieval.

## Live Demo

**Public URL:** https://aiastro-bkb4.onrender.com

```bash
curl -X POST https://aiastro-bkb4.onrender.com/api/v1/chat \
  -H "Content-Type: application/json" \
  --data-raw '{
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

**Multi-turn — second request with same `session_id`, no profile needed:**
```bash
curl -X POST https://aiastro-bkb4.onrender.com/api/v1/chat \
  -H "Content-Type: application/json" \
  --data-raw '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What about love and relationships?"
  }'
```

**Hindi response:**
```bash
curl -X POST https://aiastro-bkb4.onrender.com/api/v1/chat \
  -H "Content-Type: application/json" \
  --data-raw '{
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
    ├── RAG Engine (TF-IDF + scikit-learn cosine similarity)
    │       └── Only fires for non-chitchat intents
    │       └── Zodiac boost: +0.1 for sign-matched chunks
    │       └── Threshold gate: similarity < 0.07 → skip retrieval
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
| Vector store | scikit-learn TF-IDF + cosine similarity | Lightweight (~30MB), zero GPU dependency, fits Render free tier (512MB RAM) |
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

`user_profile` is optional after the first request in a session — the profile is cached.

**Response:**
```json
{
  "response": "As a Scorpio with strong Mars influence...",
  "zodiac": "Scorpio",
  "context_used": ["Scorpio - Career: ..."],
  "retrieval_used": true
}
```

### `GET /health`
```json
{"status": "ok", "rag_ready": true}
```

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

## Local Development

```bash
git clone https://github.com/yg2154/AIAstro.git
cd AIAstro
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Copy `.env.example` to `.env` — `OPENAI_API_KEY` is optional; the service runs fully without it using built-in stub responses.

### Docker

```bash
docker build -t aiastro .
docker run -p 8000:8000 aiastro
```
