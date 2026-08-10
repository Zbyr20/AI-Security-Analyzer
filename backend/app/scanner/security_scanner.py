from app.scanner.ssl_scanner import SSLScanner
from app.scanner.header_scanner import HeaderScanner
from app.scanner.cookie_scanner import CookieScanner
from app.scanner.dns_scanner import DNSScanner

from app.models.security_result import SecurityResult


class SecurityScanner:

    def __init__(self):
        self.ssl_scanner = SSLScanner()
        self.header_scanner = HeaderScanner()
        self.cookie_scanner = CookieScanner()
        self.dns_scanner = DNSScanner()

    def scan(self, url: str) -> SecurityResult:

        ssl_result = self.ssl_scanner.scan(url)
        header_result = self.header_scanner.scan(url)
        cookie_result = self.cookie_scanner.scan(url)
        dns_result = self.dns_scanner.scan(url)

        return SecurityResult(
            url=url,
            ssl=ssl_result,
            headers=header_result,
            cookies=cookie_result,
            dns=dns_result
        )