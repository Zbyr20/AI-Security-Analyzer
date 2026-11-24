"""SSRF koruması (TargetGuard) testleri. Gerçek DNS yerine sahte çözücü kullanılır."""
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import URLError
from urllib.request import Request

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.models.security_result import SecurityResult
from app.validators.target_guard import (
    BlockedTargetError,
    TargetGuard,
    safe_urlopen,
)


def resolver_for(mapping):
    """{"host": ["ip", ...]} sözlüğünden sahte DNS çözücü üretir."""

    def resolve(host, port):
        if host not in mapping:
            raise socket.gaierror("bulunamadı")
        return mapping[host]

    return resolve


@pytest.fixture(autouse=True)
def _koruma_acik(monkeypatch):
    monkeypatch.delenv("ALLOW_PRIVATE_TARGETS", raising=False)


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",          # loopback
        "10.0.0.5",           # özel ağ
        "172.16.3.4",
        "192.168.1.1",
        "169.254.169.254",    # bulut metadata servisi
        "100.64.0.1",         # CGNAT
        "0.0.0.0",
        "224.0.0.1",          # multicast
        "::1",
        "fe80::1%eth0",       # link-local, kapsam kimliğiyle
        "fd00::1",            # IPv6 özel (ULA)
        "::ffff:10.0.0.1",    # IPv6 içine gömülü özel IPv4
    ],
)
def test_ic_ag_adresleri_engellenir(ip):
    guard = TargetGuard(resolver=resolver_for({"hedef.test": [ip]}))
    with pytest.raises(BlockedTargetError):
        guard.check("https://hedef.test")


@pytest.mark.parametrize("ip", ["93.184.215.14", "1.1.1.1", "2606:4700:4700::1111"])
def test_herkese_acik_adresler_gecer(ip):
    guard = TargetGuard(resolver=resolver_for({"example.com": [ip]}))
    guard.check("https://example.com")  # hata atmamalı


def test_adreslerden_biri_bile_icerdeyse_engellenir():
    guard = TargetGuard(
        resolver=resolver_for({"karisik.test": ["93.184.215.14", "127.0.0.1"]})
    )
    with pytest.raises(BlockedTargetError):
        guard.check("https://karisik.test")


def test_cozulemeyen_ad_engellenmez():
    TargetGuard(resolver=resolver_for({})).check("https://yok.invalid")


def test_portlu_url_cozucuye_port_ile_gider():
    calls = []

    def resolve(host, port):
        calls.append((host, port))
        return ["1.1.1.1"]

    TargetGuard(resolver=resolve).check("https://example.com:8443/yol")
    assert calls == [("example.com", 8443)]


@pytest.mark.parametrize("value", ["1", "true", "YES", "evet"])
def test_ortam_degiskeni_korumayi_kapatir(monkeypatch, value):
    monkeypatch.setenv("ALLOW_PRIVATE_TARGETS", value)
    TargetGuard(resolver=resolver_for({"nas.local": ["192.168.1.10"]})).check(
        "http://nas.local"
    )


def test_ortam_degiskeni_yanlis_degerde_koruma_acik_kalir(monkeypatch):
    monkeypatch.setenv("ALLOW_PRIVATE_TARGETS", "0")
    with pytest.raises(BlockedTargetError):
        TargetGuard(resolver=resolver_for({"nas.local": ["192.168.1.10"]})).check(
            "http://nas.local"
        )


@pytest.mark.parametrize(
    "url",
    ["http://localhost", "http://2130706433", "http://127.1", "http://[::1]:8000"],
)
def test_gercek_cozucu_kilik_degistirmis_localhost_u_yakalar(url):
    # Ağ gerektirmez: bunlar işletim sistemi tarafından yerelde çözülür.
    with pytest.raises(BlockedTargetError):
        TargetGuard().check(url)


# --- /scan uç noktası ------------------------------------------------------


class FakeScanner:
    def __init__(self):
        self.calls = []

    def scan(self, url):
        self.calls.append(url)
        return SecurityResult(url=url, ssl={}, headers={}, cookies={})


class FakeAI:
    def generate_security_report(self, data):
        return {"summary": "ok"}


@pytest.fixture
def client(monkeypatch):
    fake = FakeScanner()
    monkeypatch.setattr(routes, "scanner", fake)
    monkeypatch.setattr(routes, "ai_service", FakeAI())
    monkeypatch.setattr(
        routes,
        "target_guard",
        TargetGuard(
            resolver=resolver_for(
                {"example.com": ["93.184.215.14"], "ic.test": ["10.1.2.3"]}
            )
        ),
    )
    with TestClient(app) as c:
        c.fake_scanner = fake
        yield c


def test_scan_ic_ag_hedefini_400_ile_reddeder(client):
    response = client.post("/scan", json={"url": "ic.test"})

    assert response.status_code == 400
    assert "ALLOW_PRIVATE_TARGETS" in response.json()["detail"]
    assert client.fake_scanner.calls == []


def test_scan_herkese_acik_hedefi_tarar(client):
    response = client.post("/scan", json={"url": "example.com"})

    assert response.status_code == 200
    assert client.fake_scanner.calls == ["https://example.com"]


# --- Yönlendirme (redirect) ile atlatma -------------------------------------


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/yonlendir":
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/gizli")
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"gizli veri")

    def log_message(self, *args):
        pass


@pytest.fixture
def yerel_sunucu():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_ic_aga_yonlendirme_engellenir(yerel_sunucu):
    with pytest.raises(URLError, match="Yönlendirme engellendi"):
        safe_urlopen(Request(yerel_sunucu + "/yonlendir"), timeout=5)


def test_koruma_kapaliyken_yonlendirme_izlenir(yerel_sunucu, monkeypatch):
    monkeypatch.setenv("ALLOW_PRIVATE_TARGETS", "1")
    with safe_urlopen(Request(yerel_sunucu + "/yonlendir"), timeout=5) as r:
        assert r.read() == b"gizli veri"
