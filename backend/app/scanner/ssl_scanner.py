import socket
import ssl
from urllib.parse import urlparse  # hostname'i almak için


class SSLScanner:

    DEFAULT_PORT = 443
    TIMEOUT = 5

    def scan(self, url: str):
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname is None:
            raise ValueError("Geçersiz hostname")
        # URL'de port varsa (ör. https://site.com:8443) onu kullan.
        # https dışındaki şemalarda (http://site.com:8080) o port TLS konuşmaz,
        # bu yüzden yalnızca https'te URL portuna bakılır.
        port = self.DEFAULT_PORT
        if parsed.scheme.lower() == "https" and parsed.port:
            port = parsed.port
        try:
            certificate = self._fetch_certificate(hostname, port)
            return self._build_result(certificate)
        except (socket.timeout, socket.gaierror, ssl.SSLError, OSError) as e:
            return {
                "ssl_valid": False,
                "certificate": None,
                "error": str(e)
            }

    def _fetch_certificate(self, hostname, port):
        # "with" blokları hata olsa bile soketleri kapatır
        # (eskiden TLS el sıkışması başarısız olunca soket açık kalıyordu).
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=self.TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssl_socket:
                return ssl_socket.getpeercert()

    def _build_result(self, certificate):
        return {
            "ssl_valid": bool(certificate),
            "certificate": certificate
        }
