from app.scanner.cookie_scanner import CookieScanner


def test_cookie_yoksa():
    for empty in (None, []):
        assert CookieScanner()._build_result(empty) == {
            "cookies_found": False,
            "cookies": [],
            "error": None,
        }


def test_guvenli_cookie_bayraklari_okunur():
    result = CookieScanner()._build_result(
        ["sid=abc; Path=/; Domain=example.com; Secure; HttpOnly; SameSite=Strict"]
    )

    assert result["cookies_found"] is True
    assert result["error"] is None
    (cookie,) = result["cookies"]
    assert cookie["name"] == "sid"
    assert cookie["secure"] is True
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Strict"
    assert cookie["domain"] == "example.com"
    assert cookie["path"] == "/"


def test_guvensiz_cookie():
    result = CookieScanner()._build_result(["tracker=1"])
    (cookie,) = result["cookies"]
    assert cookie["secure"] is False
    assert cookie["httponly"] is False
    assert cookie["samesite"] == ""


def test_birden_fazla_set_cookie():
    result = CookieScanner()._build_result(["a=1; Secure", "b=2; HttpOnly"])
    assert [c["name"] for c in result["cookies"]] == ["a", "b"]


def test_ag_hatasinda_error_doner(monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("bağlantı yok")

    monkeypatch.setattr("app.scanner.cookie_scanner.urlopen", boom)
    result = CookieScanner().scan("https://example.invalid")
    assert result["cookies_found"] is False
    assert result["cookies"] == []
    assert "bağlantı yok" in result["error"]
