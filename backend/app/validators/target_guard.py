"""SSRF koruması: tarayıcının iç ağ adreslerine istek atmasını engeller.

Bu API, kullanıcının verdiği adrese *sunucunun kendisinden* bağlanır. Koruma
olmazsa biri `http://127.0.0.1:8000`, `http://192.168.1.1` ya da bulut
sunucularındaki metadata servisi `http://169.254.169.254/` için tarama
isteyebilir; sonuçlar (açık portlar, başlıklar, çerezler) ona geri döner.
Buna SSRF (Server-Side Request Forgery) denir.

Kural: alan adı DNS ile çözülür; çıkan adreslerden *herhangi biri* herkese
açık (global) değilse hedef reddedilir. `localhost`, `2130706433`
(=127.0.0.1) veya `::ffff:10.0.0.1` gibi kılık değiştirmiş adresler de
çözümlemeden sonra yakalanır.

Yerel ağınızı bilerek taramak istiyorsanız korumayı kapatın:

    PowerShell:  $env:ALLOW_PRIVATE_TARGETS = "1"
    Bash:        export ALLOW_PRIVATE_TARGETS=1

Bilinen sınır: DNS kontrolden sonra farklı bir adres döndürürse ("DNS
rebinding") tarayıcılar yeniden çözümleme yaptığı için bu kontrol atlatılabilir.
Tam çözüm, çözülen IP'ye doğrudan bağlanmaktır; bu PR ilk ve en yaygın
saldırıları kapatır.
"""
import ipaddress
import os
import socket
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, build_opener

_TRUE_VALUES = {"1", "true", "yes", "on", "evet"}


class BlockedTargetError(ValueError):
    """Hedef iç/özel bir adrese çözülüyor."""


def private_targets_allowed() -> bool:
    return os.getenv("ALLOW_PRIVATE_TARGETS", "").strip().lower() in _TRUE_VALUES


def _is_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # "::ffff:127.0.0.1" gibi IPv6 içine gömülü IPv4'ü açıp asıl adrese bak.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    # is_global: loopback, özel (10/8, 172.16/12, 192.168/16), link-local
    # (169.254/16, metadata servisi), CGNAT (100.64/10), 0.0.0.0, belgeleme
    # aralıkları vb. için False döner. Multicast ayrıca reddedilir.
    return ip.is_global and not ip.is_multicast


def _default_resolver(host: str, port: int | None) -> list[str]:
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    return [info[4][0] for info in infos]


class TargetGuard:
    def __init__(self, resolver=None):
        # Testlerde gerçek DNS yerine sahte çözücü verilebilir.
        self._resolver = resolver or _default_resolver

    def check(self, url: str) -> None:
        """Hedef iç ağdaysa BlockedTargetError atar, değilse sessizce döner."""
        if private_targets_allowed():
            return

        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            raise BlockedTargetError("Geçersiz hedef.")

        try:
            port = parsed.port
        except ValueError:
            port = None

        try:
            addresses = self._resolver(host, port)
        except (socket.gaierror, UnicodeError):
            # Çözülemeyen ad hiçbir yere bağlanamaz; tarayıcılar zaten
            # "bulunamadı" hatası verir. Burada engellemeye gerek yok.
            return

        for address in addresses:
            # IPv6 kapsam kimliği ("fe80::1%eth0") ip_address'i bozar.
            ip = ipaddress.ip_address(address.split("%", 1)[0])
            if not _is_public(ip):
                raise BlockedTargetError(
                    "Bu adres iç ağa veya yerel makineye çözülüyor "
                    f"({ip}); güvenlik nedeniyle taranmıyor. Yerel ağı "
                    "taramak için ALLOW_PRIVATE_TARGETS=1 ayarlayın."
                )


class GuardedRedirectHandler(HTTPRedirectHandler):
    """Yönlendirmeleri de denetler.

    Herkese açık bir site `302 Location: http://169.254.169.254/` döndürerek
    ilk kontrolü atlatabilir; urllib yönlendirmeleri kendiliğinden izlediği
    için her yeni adres burada tekrar kontrol edilir.
    """

    def __init__(self, guard: TargetGuard):
        self.guard = guard

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            self.guard.check(newurl)
        except BlockedTargetError as e:
            raise URLError(f"Yönlendirme engellendi: {e}") from None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def safe_urlopen(request, timeout=10, guard: TargetGuard | None = None):
    """urlopen'ın yönlendirmeleri SSRF'e karşı denetleyen sürümü."""
    opener = build_opener(GuardedRedirectHandler(guard or TargetGuard()))
    return opener.open(request, timeout=timeout)
