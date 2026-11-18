import socket

import pytest

from app.scanner import port_scanner
from app.scanner.port_scanner import PortScanner


class _FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def fake_network(monkeypatch):
    """Ağa çıkmadan açık portları taklit eder; denenen bağlantıları kaydeder."""
    state = {"open": set(), "calls": [], "resolve": "93.184.216.34"}

    def fake_resolve(hostname):
        if isinstance(state["resolve"], Exception):
            raise state["resolve"]
        return state["resolve"]

    def fake_connect(addr, timeout=None):
        state["calls"].append((addr, timeout))
        if addr[1] in state["open"]:
            return _FakeConn()
        raise ConnectionRefusedError("refused")

    monkeypatch.setattr(port_scanner.socket, "gethostbyname", fake_resolve)
    monkeypatch.setattr(port_scanner.socket, "create_connection", fake_connect)
    return state


def test_reports_only_open_ports(fake_network):
    fake_network["open"] = {80, 443}
    result = PortScanner().scan("https://example.com")

    assert result["error"] is None
    assert result["host"] == "example.com"
    assert result["ip"] == "93.184.216.34"
    assert result["open_ports"] == [
        {"port": 80, "service": "HTTP"},
        {"port": 443, "service": "HTTPS"},
    ]
    assert result["risky_open_ports"] == []


def test_scans_every_common_port_once_in_order(fake_network):
    result = PortScanner().scan("https://example.com")
    assert result["scanned_ports"] == sorted(PortScanner.COMMON_PORTS)
    tried = sorted(addr[1] for addr, _ in fake_network["calls"])
    assert tried == sorted(PortScanner.COMMON_PORTS)


def test_connects_to_resolved_ip_with_timeout(fake_network):
    PortScanner().scan("https://example.com")
    for (host, _port), timeout in fake_network["calls"]:
        assert host == "93.184.216.34"
        assert timeout == PortScanner.TIMEOUT


def test_flags_risky_open_ports(fake_network):
    fake_network["open"] = {443, 3306, 6379}
    result = PortScanner().scan("https://example.com")

    risky = {r["port"]: r for r in result["risky_open_ports"]}
    assert set(risky) == {3306, 6379}
    assert risky[3306]["service"] == "MySQL"
    assert risky[6379]["reason"]


def test_every_risky_port_is_scanned_by_default():
    assert set(PortScanner.RISKY_PORTS) <= set(PortScanner.COMMON_PORTS)


def test_url_port_and_path_do_not_change_target_host(fake_network):
    result = PortScanner().scan("https://Example.com:8443/login?x=1")
    assert result["host"] == "example.com"
    assert result["error"] is None


def test_timeouts_count_as_closed(fake_network, monkeypatch):
    def timeout_connect(addr, timeout=None):
        raise socket.timeout("timed out")

    monkeypatch.setattr(port_scanner.socket, "create_connection", timeout_connect)
    result = PortScanner().scan("https://example.com")
    assert result["open_ports"] == []
    assert result["error"] is None


def test_unresolvable_host_returns_error_without_connecting(fake_network):
    fake_network["resolve"] = socket.gaierror("Name or service not known")
    result = PortScanner().scan("https://nope.invalid")

    assert result["error"] and "nope.invalid" in result["error"]
    assert result["open_ports"] == []
    assert fake_network["calls"] == []


def test_invalid_url_returns_error(fake_network):
    result = PortScanner().scan("not a url")
    assert result["error"] == "Geçersiz hostname."
    assert fake_network["calls"] == []


def test_custom_port_list(fake_network):
    fake_network["open"] = {9000}
    result = PortScanner(ports={9000: "Custom", 9001: "Other"}).scan("http://example.com")
    assert result["scanned_ports"] == [9000, 9001]
    assert result["open_ports"] == [{"port": 9000, "service": "Custom"}]
    assert result["risky_open_ports"] == []


def test_real_local_listener():
    """Ağ sahtesi olmadan: yerelde açılan bir dinleyici 'açık', kapalı port 'kapalı'."""
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        open_port = server.getsockname()[1]

        with socket.socket() as tmp:
            tmp.bind(("127.0.0.1", 0))
            closed_port = tmp.getsockname()[1]

        scanner = PortScanner(ports={open_port: "test", closed_port: "kapalı"})
        result = scanner.scan("http://127.0.0.1")

    assert result["open_ports"] == [{"port": open_port, "service": "test"}]
