"""TLSScanner testleri. Gerçek ağ kullanılmaz; soket ve el sıkışması sahte."""
import socket
import ssl

import pytest

from app.models.security_result import SecurityResult
from app.scanner import tls_scanner
from app.scanner.tls_scanner import TLSScanner


def _fake_probe(supported, calls=None):
    """Yalnızca `supported` içindeki sürümleri kabul eden sahte _probe."""

    def probe(self, hostname, port, version):
        if calls is not None:
            calls.append((hostname, port, version))
        return version in supported

    return probe


def test_modern_sunucu_sadece_tls12_ve_13(monkeypatch):
    monkeypatch.setattr(
        TLSScanner,
        "_probe",
        _fake_probe({ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3}),
    )
    result = TLSScanner().scan("https://example.com")

    assert result == {
        "host": "example.com",
        "port": 443,
        "protocols": {
            "TLSv1.0": False,
            "TLSv1.1": False,
            "TLSv1.2": True,
            "TLSv1.3": True,
        },
        "highest_protocol": "TLSv1.3",
        "weak_protocols": [],
        "supports_tls13": True,
        "error": None,
    }


def test_eski_surumleri_kabul_eden_sunucu_zayif_olarak_isaretlenir(monkeypatch):
    monkeypatch.setattr(
        TLSScanner,
        "_probe",
        _fake_probe({ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_2}),
    )
    result = TLSScanner().scan("https://eski.example.com")

    assert result["weak_protocols"] == ["TLSv1.0", "TLSv1.1"]
    assert result["highest_protocol"] == "TLSv1.2"
    assert result["supports_tls13"] is False


def test_denenemeyen_surum_none_olur_ve_zayif_sayilmaz(monkeypatch):
    def probe(self, hostname, port, version):
        if version == ssl.TLSVersion.TLSv1:
            return None
        return version == ssl.TLSVersion.TLSv1_3

    monkeypatch.setattr(TLSScanner, "_probe", probe)
    result = TLSScanner().scan("https://example.com")

    assert result["protocols"]["TLSv1.0"] is None
    assert result["weak_protocols"] == []
    assert result["highest_protocol"] == "TLSv1.3"


@pytest.mark.parametrize(
    "url, port",
    [
        ("https://example.com:8443/yol", 8443),
        ("http://example.com:8080", 443),
        ("example.com", 443),
    ],
)
def test_port_secimi_ssl_tarayici_ile_ayni(monkeypatch, url, port):
    calls = []
    monkeypatch.setattr(TLSScanner, "_probe", _fake_probe(set(), calls))
    TLSScanner().scan(url if "://" in url else "https://" + url)

    assert {c[1] for c in calls} == {port}
    assert len(calls) == len(TLSScanner.PROTOCOLS)


def test_gecersiz_hostname():
    result = TLSScanner().scan("https://")
    assert result["error"] == "Geçersiz hostname."
    assert result["protocols"] == {}


def test_baglanti_kurulamazsa_hata_doner_ve_denemeyi_keser(monkeypatch):
    attempts = []

    def refuse(address, timeout):
        attempts.append(address)
        raise ConnectionRefusedError("bağlantı reddedildi")

    monkeypatch.setattr(tls_scanner.socket, "create_connection", refuse)
    result = TLSScanner().scan("https://kapali.example.com")

    assert "bağlanılamadı" in result["error"]
    assert result["protocols"] == {}
    assert result["supports_tls13"] is False
    assert attempts == [("kapali.example.com", 443)]


class _FakeSocket:
    def __init__(self):
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True


class _FakeContext:
    def __init__(self, error):
        self.error = error

    def wrap_socket(self, sock, server_hostname):
        if self.error:
            raise self.error
        return _FakeSocket()


@pytest.mark.parametrize(
    "error, expected",
    [
        (None, True),
        (ssl.SSLError(1, "[SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert"), False),
        (ConnectionResetError("reset"), False),
        (socket.timeout("timed out"), False),
        (ssl.SSLError(1, "[SSL: NO_PROTOCOLS_AVAILABLE] no protocols"), None),
    ],
)
def test_probe_el_sikismasi_sonucu_ve_soket_kapanir(monkeypatch, error, expected):
    sock = _FakeSocket()
    monkeypatch.setattr(tls_scanner.socket, "create_connection", lambda *a, **k: sock)
    monkeypatch.setattr(TLSScanner, "_make_context", lambda self, v: _FakeContext(error))

    assert TLSScanner()._probe("example.com", 443, ssl.TLSVersion.TLSv1_2) is expected
    assert sock.closed is True


def test_context_surume_kilitlenir_ve_sertifika_dogrulamaz():
    context = TLSScanner()._make_context(ssl.TLSVersion.TLSv1_3)

    assert context.minimum_version == ssl.TLSVersion.TLSv1_3
    assert context.maximum_version == ssl.TLSVersion.TLSv1_3
    assert context.verify_mode == ssl.CERT_NONE
    assert context.check_hostname is False


def test_security_result_tls_alani():
    assert SecurityResult("u", {}, {}, {}).to_dict()["tls"] == {}
    data = SecurityResult("u", {}, {}, {}, tls={"supports_tls13": True}).to_dict()
    assert data["tls"] == {"supports_tls13": True}
