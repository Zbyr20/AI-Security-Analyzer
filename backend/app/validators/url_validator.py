import ipaddress
import re
from urllib.parse import urlparse

# Bir DNS etiketi: 1-63 karakter, harf/rakam/tire; tireyle başlayıp bitemez.
# Alt çizgi DNS'te hostname için standart dışıdır ama gerçek sitelerde görülür
# ve tarayıcılar kabul eder, bu yüzden izin veriyoruz.
_LABEL_RE = re.compile(r"^(?!-)[a-z0-9_-]{1,63}(?<!-)$")


class URLValidator:
    def _normalize(self, url: str) -> str:
        url = url.strip()

        if not url:
            raise ValueError("URL boş olamaz.")

        # Baştaki/sondaki boşluklar temizlendi; içeride kalan boşluk veya
        # kontrol karakteri (\n, \t, \x00 ...) geçerli bir URL'de olamaz.
        # Örn. "not a url" eskiden "https://not a url" olarak taranıyordu.
        if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in url):
            raise ValueError("URL boşluk veya kontrol karakteri içeremez.")

        # Şema büyük/küçük harf duyarsızdır (RFC 3986): "HTTPS://" de geçerli.
        if url.lower().startswith(("http://", "https://")):
            return url

        if "://" in url:
            raise ValueError("Desteklenmeyen URL protokolü.")

        return "https://" + url

    def _check_hostname(self, hostname: str) -> None:
        # IP adresi (IPv4 veya köşeli parantezli IPv6) olduğu gibi kabul edilir.
        try:
            ipaddress.ip_address(hostname)
            return
        except ValueError:
            pass

        # Türkçe/Unicode alan adları (örn. "bücher.de") IDNA ile ASCII'ye
        # (punycode, "xn--...") çevrilip öyle kontrol edilir.
        try:
            ascii_host = hostname.encode("idna").decode("ascii")
        except UnicodeError:
            raise ValueError("Geçersiz alan adı.") from None

        # Sondaki nokta ("example.com.") DNS'te geçerli tam addır.
        if ascii_host.endswith("."):
            ascii_host = ascii_host[:-1]

        if not ascii_host or len(ascii_host) > 253:
            raise ValueError("Geçersiz alan adı.")
        if not all(_LABEL_RE.match(label) for label in ascii_host.split(".")):
            raise ValueError("Geçersiz alan adı.")

    def validate(self, url: str) -> str:
        url = self._normalize(url)

        try:
            parsed = urlparse(url)
            # .port, sayı olmayan ("abc") veya 0-65535 dışı portta ValueError atar.
            port = parsed.port
        except ValueError:
            raise ValueError("Geçersiz URL veya port.") from None

        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError("Desteklenmeyen URL protokolü.")
        if not parsed.hostname:
            raise ValueError("Geçersiz alan adı.")
        if port == 0:
            raise ValueError("Geçersiz URL veya port.")

        # "https://google.com@evil.com" gerçekte evil.com'a gider; kullanıcıyı
        # yanıltan bu biçimi ve URL'e gömülü parolaları reddediyoruz.
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Kullanıcı adı veya parola içeren URL desteklenmiyor.")

        self._check_hostname(parsed.hostname)

        return url

    def validator(self, url: str) -> str:
        return self.validate(url)
