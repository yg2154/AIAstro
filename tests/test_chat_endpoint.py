import pytest
import uuid
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "rag_ready" in data


@pytest.mark.anyio
async def test_chat_with_profile(client):
    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "message": "What career suits me?",
        "user_profile": {
            "name": "Priya",
            "birth_date": "1992-11-15",
            "birth_time": "14:30",
            "birth_place": "Mumbai",
            "preferred_language": "en",
        },
    }
    resp = await client.post("/api/v1/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert data["zodiac"] == "Scorpio"
    assert isinstance(data["retrieval_used"], bool)
    assert isinstance(data["context_used"], list)


@pytest.mark.anyio
async def test_chat_session_memory(client):
    session_id = str(uuid.uuid4())
    # First request with profile
    await client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "Tell me about my zodiac.",
            "user_profile": {
                "name": "Arjun",
                "birth_date": "1988-03-25",
                "preferred_language": "en",
            },
        },
    )
    # Second request without profile — session should remember
    resp = await client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "What about my career?",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["zodiac"] == "Aries"


@pytest.mark.anyio
async def test_chat_hindi_response(client):
    session_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "मेरे करियर के बारे में बताएं",
            "user_profile": {
                "name": "Ravi",
                "birth_date": "1995-08-10",
                "preferred_language": "hi",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["zodiac"] == "Leo"
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0


@pytest.mark.anyio
async def test_invalid_birth_date(client):
    resp = await client.post(
        "/api/v1/chat",
        json={
            "session_id": str(uuid.uuid4()),
            "message": "Hello",
            "user_profile": {
                "name": "Test",
                "birth_date": "not-a-date",
                "preferred_language": "en",
            },
        },
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_chitchat_no_retrieval(client):
    session_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "Hello! What is your name?",
            "user_profile": {
                "name": "Test",
                "birth_date": "1990-06-15",
                "preferred_language": "en",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    # Chitchat should not trigger retrieval
    assert data["retrieval_used"] is False
