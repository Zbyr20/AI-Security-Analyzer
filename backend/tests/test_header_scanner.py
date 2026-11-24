from email.message import Message

from app.scanner.header_scanner import HeaderScanner


def _headers(**pairs):
    msg = Message()
    for name, value in pairs.items():
        msg[name.replace("_", "-")] = value
    return msg


def test_tum_guvenlik_headerlari_var():
    headers = _headers(
        Content_Security_Policy="default-src 'self'",
        Strict_Transport_Security="max-age=31536000",
        X_Frame_Options="DENY",
        X_Content_Type_Options="nosniff",
        Referrer_Policy="no-referrer",
        Permissions_Policy="camera=()",
    )
    result = HeaderScanner()._build_result(headers)

    assert result["error"] is None
    for key in HeaderScanner.SECURITY_HEADERS.values():
        assert result[key] is True


def test_eksik_headerlar_false_doner():
    result = HeaderScanner()._build_result(_headers(Server="nginx"))

    assert result["error"] is None
    assert set(result) == {"error", *HeaderScanner.SECURITY_HEADERS.values()}
    assert not any(result[k] for k in HeaderScanner.SECURITY_HEADERS.values())


def test_header_adlari_buyuk_kucuk_harf_duyarsiz():
    result = HeaderScanner()._build_result({"STRICT-TRANSPORT-SECURITY": "max-age=1"})
    assert result["hsts"] is True
    assert result["csp"] is False


def test_ag_hatasinda_error_doner(monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("bağlantı yok")

    monkeypatch.setattr("app.scanner.header_scanner.safe_urlopen", boom)
    assert HeaderScanner().scan("https://example.invalid") == {
        "error": "Headerlar taranamadı!!"
    }
