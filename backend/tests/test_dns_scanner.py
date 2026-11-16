import dns.resolver
import pytest

from app.scanner import dns_scanner
from app.scanner.dns_scanner import DNSScanner


class FakeAnswer:
    def __init__(self, text):
        self.text = text

    def to_text(self):
        return self.text


def fake_resolver(monkeypatch, records):
    """records: {"A": ["1.2.3.4"], "MX": Exception(...)} — olmayan tip NoAnswer verir."""
    calls = []

    def resolve(hostname, record_type):
        calls.append((hostname, record_type))
        value = records.get(record_type, dns.resolver.NoAnswer())
        if isinstance(value, Exception):
            raise value
        return [FakeAnswer(v) for v in value]

    monkeypatch.setattr(dns_scanner.dns.resolver, "resolve", resolve)
    return calls


def test_kayitlar_kucuk_harfli_anahtarlara_yazilir(monkeypatch):
    calls = fake_resolver(monkeypatch, {
        "A": ["93.184.216.34"],
        "AAAA": ["2606:2800:220:1::1"],
        "MX": ["10 mail.example.com."],
        "NS": ["a.iana-servers.net.", "b.iana-servers.net."],
    })

    result = DNSScanner().scan("https://Example.com:8443/yol?q=1")

    assert result == {
        "domain": "example.com",
        "a": ["93.184.216.34"],
        "aaaa": ["2606:2800:220:1::1"],
        "mx": ["10 mail.example.com."],
        "ns": ["a.iana-servers.net.", "b.iana-servers.net."],
        "cname": [],
        "error": None,
    }
    assert [t for _, t in calls] == DNSScanner.RECORD_TYPES
    assert {h for h, _ in calls} == {"example.com"}


@pytest.mark.parametrize("error", [dns.resolver.NoAnswer(), dns.resolver.NXDOMAIN(), dns.resolver.NoNameservers()])
def test_beklenen_dns_hatalari_sessizce_atlanir(monkeypatch, error):
    fake_resolver(monkeypatch, {t: error for t in DNSScanner.RECORD_TYPES})

    result = DNSScanner().scan("https://yok.example")

    assert result["error"] is None
    assert all(result[t.lower()] == [] for t in DNSScanner.RECORD_TYPES)


def test_beklenmeyen_hata_error_alanina_yazilir_diger_kayitlar_korunur(monkeypatch):
    fake_resolver(monkeypatch, {
        "A": ["1.2.3.4"],
        "MX": dns.resolver.LifetimeTimeout(timeout=5.0, errors={}),
    })

    result = DNSScanner().scan("https://example.com")

    assert result["a"] == ["1.2.3.4"]
    assert result["mx"] == []
    assert result["error"]


def test_hostname_yoksa_error_doner():
    assert DNSScanner().scan("https://") == {"error": "Geçersiz hostname."}
