"""/scan uç noktası testleri. Ağ ve yapay zekâ çağrıları sahte nesnelerle değiştirilir."""
import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.models.security_result import SecurityResult


class FakeScanner:
    def __init__(self):
        self.calls = []

    def scan(self, url):
        self.calls.append(url)
        return SecurityResult(url=url, ssl={"ssl_valid": True}, headers={}, cookies={})


class FakeAI:
    def generate_security_report(self, data):
        return {"summary": f"rapor: {data['url']}"}


@pytest.fixture
def client(monkeypatch):
    fake = FakeScanner()
    monkeypatch.setattr(routes, "scanner", fake)
    monkeypatch.setattr(routes, "ai_service", FakeAI())
    with TestClient(app) as c:
        c.fake_scanner = fake
        yield c


def test_root(client):
    assert client.get("/").json() == {"message": "AI Security Analyzer API is running"}


def test_scan_basarili(client):
    response = client.post("/scan", json={"url": "example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["url"] == "https://example.com"
    assert body["scan"]["ssl"] == {"ssl_valid": True}
    assert body["report"] == {"summary": "rapor: https://example.com"}
    assert client.fake_scanner.calls == ["https://example.com"]


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com",
        "",
        "https://",
        "not a url",
        "https://example.com:99999",
        "https://google.com@evil.com",
    ],
)
def test_gecersiz_url_400_doner_ve_tarama_yapilmaz(client, url):
    response = client.post("/scan", json={"url": url})

    assert response.status_code == 400
    assert response.json()["detail"]
    assert client.fake_scanner.calls == []


def test_url_alani_eksikse_422(client):
    assert client.post("/scan", json={}).status_code == 422


def test_tarama_hatasi_500_doner(client, monkeypatch):
    def boom(url):
        raise RuntimeError("tarayıcı çöktü")

    monkeypatch.setattr(client.fake_scanner, "scan", boom)
    response = client.post("/scan", json={"url": "example.com"})

    assert response.status_code == 500
    assert response.json()["detail"] == "tarayıcı çöktü"
