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
