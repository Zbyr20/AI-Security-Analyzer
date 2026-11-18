import socket
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse


class PortScanner:
    """Hedef sunucuda yaygın servis portlarının açık olup olmadığını kontrol eder.

    Yalnızca TCP bağlantısı kurulup hemen kapatılır (connect scan); servise
    veri gönderilmez. Liste bilerek kısa tutuldu: amaç, bir web sitesinin
    internete gereksiz yere açık bıraktığı servisleri (veritabanı, RDP, Telnet
    gibi) fark etmek, kapsamlı bir ağ taraması yapmak değil.
    """

    TIMEOUT = 2
    MAX_WORKERS = 16

    # port -> servis adı
    COMMON_PORTS = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        445: "SMB",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        6379: "Redis",
        8080: "HTTP-Alt",
        8443: "HTTPS-Alt",
        9200: "Elasticsearch",
        27017: "MongoDB",
    }

    # İnternete açık olması genellikle risk sayılan servisler.
    RISKY_PORTS = {
        21: "FTP şifreleri açık metin gönderir.",
        23: "Telnet şifrelemesizdir; SSH kullanılmalı.",
        445: "SMB internete açık olmamalı (fidye yazılımı hedefi).",
        3306: "Veritabanı doğrudan internete açık.",
        3389: "RDP kaba kuvvet saldırılarının sık hedefidir.",
        5432: "Veritabanı doğrudan internete açık.",
        6379: "Redis varsayılan olarak kimlik doğrulamasız çalışır.",
        9200: "Elasticsearch varsayılan olarak kimlik doğrulamasız çalışabilir.",
        27017: "MongoDB doğrudan internete açık.",
    }

    def __init__(self, ports: dict | None = None):
        self.ports = ports if ports is not None else self.COMMON_PORTS

    def scan(self, url: str) -> dict:
        hostname = urlparse(url).hostname
        if not hostname:
            return self._error_result(None, "Geçersiz hostname.")

        # Adı bir kez çöz: her port için ayrı DNS sorgusu yapılmasın ve
        # çözülemeyen adda tüm portlar "kapalı" görünmesin.
        try:
            address = socket.gethostbyname(hostname)
        except OSError as e:
            return self._error_result(hostname, f"{hostname} çözümlenemedi: {e}")

        ports = sorted(self.ports)
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as pool:
            states = list(pool.map(lambda p: self._is_open(address, p), ports))

        open_ports = [p for p, is_open in zip(ports, states) if is_open]
        return self._build_result(hostname, address, ports, open_ports)

    def _is_open(self, address: str, port: int) -> bool:
        try:
            with socket.create_connection((address, port), timeout=self.TIMEOUT):
                return True
        except OSError:
            # Reddedildi, zaman aşımı veya filtrelendi: hepsi "açık değil".
            return False

    def _build_result(self, hostname, address, ports, open_ports) -> dict:
        return {
            "host": hostname,
            "ip": address,
            "scanned_ports": ports,
            "open_ports": [
                {"port": p, "service": self.ports.get(p, "bilinmiyor")}
                for p in open_ports
            ],
            "risky_open_ports": [
                {
                    "port": p,
                    "service": self.ports.get(p, "bilinmiyor"),
                    "reason": self.RISKY_PORTS[p],
                }
                for p in open_ports
                if p in self.RISKY_PORTS
            ],
            "error": None,
        }

    def _error_result(self, hostname, message) -> dict:
        return {
            "host": hostname,
            "ip": None,
            "scanned_ports": [],
            "open_ports": [],
            "risky_open_ports": [],
            "error": message,
        }
