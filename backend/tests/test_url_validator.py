import pytest

from app.validators.url_validator import URLValidator


@pytest.fixture
def validator():
    return URLValidator()


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("example.com", "https://example.com"),
        ("  example.com  ", "https://example.com"),
        ("http://example.com", "http://example.com"),
        ("https://example.com/path?q=1", "https://example.com/path?q=1"),
        ("HTTPS://Example.com", "HTTPS://Example.com"),
        ("sub.example.com:8443", "https://sub.example.com:8443"),
    ],
)
def test_gecerli_urller(validator, raw, expected):
    assert validator.validate(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["ftp://example.com", "file:///etc/passwd", "javascript://alert(1)"],
)
def test_desteklenmeyen_protokol(validator, raw):
    with pytest.raises(ValueError, match="protokol"):
        validator.validate(raw)


@pytest.mark.parametrize("raw", ["", "   "])
def test_bos_url(validator, raw):
    with pytest.raises(ValueError, match="boş"):
        validator.validate(raw)


@pytest.mark.parametrize("raw", ["https://", "http:///yol"])
def test_hostname_yok(validator, raw):
    with pytest.raises(ValueError, match="alan adı"):
        validator.validate(raw)


def test_eski_isim_validator_hala_calisiyor(validator):
    assert validator.validator("example.com") == "https://example.com"


@pytest.mark.parametrize(
    "raw",
    [
        "not a url",
        "exa mple.com",
        "https://example.com/a b",
        "example.com\n/x",
        "https://exam\tple.com",
        "https://example.com\x00.evil",
        "https://example\x7f.com",
    ],
)
def test_bosluk_ve_kontrol_karakteri_reddedilir(validator, raw):
    with pytest.raises(ValueError, match="boşluk veya kontrol"):
        validator.validate(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "https://example.com:99999",
        "https://example.com:abc",
        "https://example.com:0",
        "example.com:-1",
        "https://[gecersiz-ipv6]",
    ],
)
def test_gecersiz_port_veya_url(validator, raw):
    with pytest.raises(ValueError, match="port"):
        validator.validate(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "https://-bad.com",
        "https://bad-.com",
        "https://a..b.com",
        "https://.example.com",
        "https://exa!mple.com",
        "https://" + "a" * 64 + ".com",
        "https://" + ".".join(["a" * 63] * 4) + ".com",
    ],
)
def test_gecersiz_alan_adi(validator, raw):
    with pytest.raises(ValueError, match="alan adı"):
        validator.validate(raw)


@pytest.mark.parametrize(
    "raw",
    ["https://user:pw@example.com", "https://google.com@evil.com", "admin@example.com"],
)
def test_kullanici_bilgisi_iceren_url_reddedilir(validator, raw):
    with pytest.raises(ValueError, match="Kullanıcı adı veya parola"):
        validator.validate(raw)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("https://example.com.", "https://example.com."),
        ("https://ex_ample.com", "https://ex_ample.com"),
        ("127.0.0.1", "https://127.0.0.1"),
        ("https://[::1]:8080", "https://[::1]:8080"),
        ("bücher.de", "https://bücher.de"),
        ("Örnek.com.tr", "https://Örnek.com.tr"),
        ("https://xn--bcher-kva.example", "https://xn--bcher-kva.example"),
        ("https://example.com:65535/x?y=1#z", "https://example.com:65535/x?y=1#z"),
        ("https://" + "a" * 63 + ".com", "https://" + "a" * 63 + ".com"),
    ],
)
def test_sinirda_kalan_gecerli_urller(validator, raw, expected):
    assert validator.validate(raw) == expected
