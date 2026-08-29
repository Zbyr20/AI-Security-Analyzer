class SecurityResult:

    def __init__(
        self,
        url: str,
        ssl: dict,
        headers: dict,
        cookies: dict,
        dns: dict | None = None,
    ):
        self.url = url
        self.ssl = ssl
        self.headers = headers
        self.cookies = cookies
        self.dns = dns or {}

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "ssl": self.ssl,
            "headers": self.headers,
            "cookies": self.cookies,
            "dns": self.dns,
        }