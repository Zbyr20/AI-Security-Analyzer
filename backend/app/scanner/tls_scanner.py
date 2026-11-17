import socket
import ssl
import warnings
from urllib.parse import urlparse


class TLSScanner:
    """Sunucunun hangi TLS protokol sürümlerini kabul ettiğini test eder.

    Her sürüm için ayrı bir bağlantı açılır ve el sıkışması yalnızca o sürüme
    kilitlenir. Sertifika doğrulaması burada bilerek kapalıdır: sertifikayı
    SSLScanner kontrol eder, bu tarayıcı yalnızca protokol desteğine bakar.
    """

    DEFAULT_PORT = 443
    TIMEOUT = 5

    PROTOCOLS = {
        "TLSv1.0": ssl.TLSVersion.TLSv1,
        "TLSv1.1": ssl.TLSVersion.TLSv1_1,
        "TLSv1.2": ssl.TLSVersion.TLSv1_2,
        "TLSv1.3": ssl.TLSVersion.TLSv1_3,
    }

    # 2021'de RFC 8996 ile kullanımdan kaldırılan sürümler.
    WEAK_PROTOCOLS = ("TLSv1.0", "TLSv1.1")

    def scan(self, url: str) -> dict:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return self._error_result(None, None, "Geçersiz hostname.")

        # SSLScanner ile aynı kural: yalnızca https URL'sindeki port TLS konuşur.
        port = self.DEFAULT_PORT
        if parsed.scheme.lower() == "https" and parsed.port:
            port = parsed.port

        protocols = {}
        for name, version in self.PROTOCOLS.items():
            try:
                protocols[name] = self._probe(hostname, port, version)
            except ConnectionError as e:
                # TCP bağlantısı hiç kurulamadı: sunucuya ulaşılamıyor,
                # diğer sürümleri denemenin anlamı yok.
                return self._error_result(hostname, port, str(e))

        return self._build_result(hostname, port, protocols)

    def _probe(self, hostname: str, port: int, version: ssl.TLSVersion):
        """True: sürüm kabul edildi, False: reddedildi,
        None: bu makinedeki Python/OpenSSL o sürümü deneyemiyor."""
        context = self._make_context(version)
        if context is None:
            return None

        try:
            sock = socket.create_connection((hostname, port), timeout=self.TIMEOUT)
        except OSError as e:
            raise ConnectionError(f"{hostname}:{port} adresine bağlanılamadı: {e}") from e

        with sock:
            try:
                with context.wrap_socket(sock, server_hostname=hostname):
                    return True
            except ssl.SSLError as e:
                if "NO_PROTOCOLS_AVAILABLE" in str(e).upper():
                    return None
                return False
            except OSError:
                # Bazı sunucular desteklemedikleri sürümde bağlantıyı
                # kapatır/sıfırlar ya da cevap vermez (timeout).
                return False

    def _make_context(self, version: ssl.TLSVersion):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        if version < ssl.TLSVersion.TLSv1_2:
            # Güncel OpenSSL eski sürümleri varsayılan güvenlik seviyesinde
            # istemci tarafında engeller; sunucuyu test edebilmek için düşür.
            try:
                context.set_ciphers("DEFAULT:@SECLEVEL=0")
            except ssl.SSLError:
                return None
        try:
            # Python eski sürümleri seçince DeprecationWarning verir; burada
            # bilerek seçiyoruz (amaç sunucunun onları kabul edip etmediği).
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                context.minimum_version = version
                context.maximum_version = version
        except (ValueError, ssl.SSLError):
            return None
        return context

    def _build_result(self, hostname: str, port: int, protocols: dict) -> dict:
        supported = [name for name, ok in protocols.items() if ok]
        return {
            "host": hostname,
            "port": port,
            "protocols": protocols,
            "highest_protocol": supported[-1] if supported else None,
            "weak_protocols": [
                name for name in self.WEAK_PROTOCOLS if protocols.get(name)
            ],
            "supports_tls13": protocols.get("TLSv1.3") is True,
            "error": None,
        }

    def _error_result(self, hostname, port, message: str) -> dict:
        return {
            "host": hostname,
            "port": port,
            "protocols": {},
            "highest_protocol": None,
            "weak_protocols": [],
            "supports_tls13": False,
            "error": message,
        }
