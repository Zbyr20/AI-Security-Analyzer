import socket
import ssl

import pytest

from app.scanner import ssl_scanner
from app.scanner.ssl_scanner import SSLScanner


class FakeSocket:
    def __init__(self, cert=None):
        self.cert = cert
        self.closed = False

    def getpeercert(self):
        return self.cert

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class FakeContext:
    def __init__(self, cert=None, error=None):
        self.cert = cert
        self.error = error
        self.server_hostname = None
        self.wrapped = None

    def wrap_socket(self, sock, server_hostname):
        self.server_hostname = server_hostname
        if self.error:
            raise self.error
        self.wrapped = FakeSocket(self.cert)
        return self.wrapped


@pytest.fixture
def fake_net(monkeypatch):
    """Ağa çıkmadan socket/ssl çağrılarını kaydeder."""
    state = {"address": None, "raw": None, "context": FakeContext(cert={"subject": "x"})}

    def create_connection(address, timeout):
        state["address"] = address
        state["timeout"] = timeout
        state["raw"] = FakeSocket()
        return state["raw"]

    monkeypatch.setattr(ssl_scanner.socket, "create_connection", create_connection)
    monkeypatch.setattr(ssl_scanner.ssl, "create_default_context", lambda: state["context"])
    return state


def test_gecerli_sertifika(fake_net):
    cert = {"subject": ((("commonName", "example.com"),),), "notAfter": "Jan  1 00:00:00 2030 GMT"}
    fake_net["context"] = FakeContext(cert=cert)

    result = SSLScanner().scan("https://example.com/giris")

    assert result == {"ssl_valid": True, "certificate": cert}
    assert fake_net["address"] == ("example.com", 443)
    assert fake_net["context"].server_hostname == "example.com"


def test_bos_sertifika_gecersiz_sayilir(fake_net):
    fake_net["context"] = FakeContext(cert={})
    assert SSLScanner().scan("https://example.com")["ssl_valid"] is False


def test_https_urlsindeki_port_kullanilir(fake_net):
    SSLScanner().scan("https://example.com:8443/")
    assert fake_net["address"] == ("example.com", 8443)


def test_http_urlsinde_port_yerine_443_denenir(fake_net):
    SSLScanner().scan("http://example.com:8080/")
    assert fake_net["address"] == ("example.com", 443)


def test_basarili_taramada_soketler_kapanir(fake_net):
    SSLScanner().scan("https://example.com")
    assert fake_net["raw"].closed
    assert fake_net["context"].wrapped.closed


def test_tls_hatasinda_ham_soket_kapanir_ve_error_doner(fake_net):
    fake_net["context"] = FakeContext(error=ssl.SSLCertVerificationError("self-signed certificate"))

    result = SSLScanner().scan("https://self-signed.example")

    assert result["ssl_valid"] is False
    assert result["certificate"] is None
    assert "self-signed" in result["error"]
    assert fake_net["raw"].closed  # eskiden bu soket açık kalıyordu


@pytest.mark.parametrize("error", [socket.timeout("timed out"), socket.gaierror("Name or service not known"), ConnectionRefusedError("refused")])
def test_baglanti_hatalari_error_olarak_doner(monkeypatch, error):
    def boom(*args, **kwargs):
        raise error

    monkeypatch.setattr(ssl_scanner.socket, "create_connection", boom)
    result = SSLScanner().scan("https://example.invalid")

    assert result == {"ssl_valid": False, "certificate": None, "error": str(error)}


def test_hostname_yoksa_valueerror():
    with pytest.raises(ValueError):
        SSLScanner().scan("https://")
