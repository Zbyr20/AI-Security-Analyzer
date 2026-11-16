from urllib.parse import urlparse


class URLValidator:
    def _normalize(self, url: str) -> str:
        url = url.strip()

        if not url:
            raise ValueError("URL boş olamaz.")

        # Şema büyük/küçük harf duyarsızdır (RFC 3986): "HTTPS://" de geçerli.
        if url.lower().startswith(("http://", "https://")):
            return url

        if "://" in url:
            raise ValueError("Desteklenmeyen URL protokolü.")

        return "https://" + url

    def validate(self, url: str) -> str:
        url = self._normalize(url)
        parsed = urlparse(url)

        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError("Desteklenmeyen URL protokolü.")
        if not parsed.hostname:
            raise ValueError("Geçersiz alan adı.")

        return url

    def validator(self, url: str) -> str:
        return self.validate(url)
