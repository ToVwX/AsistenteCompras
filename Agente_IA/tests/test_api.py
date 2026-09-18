import os

os.environ["AGENT_PROVIDER"] = "mock"

from fastapi.testclient import TestClient

from app.main import app
from app.tools import verificar_compatibilidad


client = TestClient(app)


def test_frontend_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "CompraTech" in response.text
    assert "/static/bot-compratech.png" in response.text


def test_frontend_assets_are_served() -> None:
    styles = client.get("/static/styles.css")
    script = client.get("/static/app.js")
    assert styles.status_code == 200
    assert "overflow-y: auto" in styles.text
    assert script.status_code == 200
    assert "preferredSpanishVoice" in script.text
    assert "Escuchar" in script.text


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["provider"] == "mock"


def test_chat_returns_mock_response() -> None:
    response = client.post(
        "/chat",
        json={
            "message": "Busco audifonos inalambricos por menos de 1500 pesos",
            "session_id": "test",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "test"
    assert payload["provider"] == "mock"
    assert payload["response"]


def test_chat_rejects_blank_message() -> None:
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422


def test_reset_session() -> None:
    response = client.delete("/sessions/test")
    assert response.status_code == 200
    assert response.json()["session_id"] == "test"


def test_xbox_bluetooth_compatibility_warning() -> None:
    result = verificar_compatibilidad.invoke(
        {
            "periferico": "audifonos",
            "plataforma": "Xbox Series S",
            "conexion": "Bluetooth",
        }
    )
    assert "Bluetooth generico" in result
    assert "Xbox" in result


def test_chat_redirects_topics_unrelated_to_peripherals() -> None:
    response = client.post(
        "/chat",
        json={
            "message": "Explicame como cocinar una pizza",
            "session_id": "fuera-de-dominio",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "Solo puedo ayudarte" in payload["response"]
    assert "perifericos" in payload["response"]
    assert payload["tools_used"] == []
