from urllib.request import Request, urlopen
from http.cookies import SimpleCookie


class CookieScanner:

    def scan(self, url: str) -> dict:
        try:
            request = Request(
                url,
                method="GET",
                headers={
                    "User-Agent": "AI-Security-Analyzer/1.0"
                }
            )

            with urlopen(request, timeout=10) as response:
                cookies = response.headers.get_all("Set-Cookie")

            return self._build_result(cookies)

        except Exception as e:
            return {
                "cookies_found": False,
                "cookies": [],
                "error": str(e)
            }

    def _build_result(self, cookies) -> dict:

        if not cookies:
            return {
                "cookies_found": False,
                "cookies": [],
                "error": None
            }

        parsed_cookies = []

        for cookie_string in cookies:

            cookie = SimpleCookie()
            cookie.load(cookie_string)

            for name, morsel in cookie.items():

                parsed_cookies.append({
                    "name": name,
                    "secure": bool(morsel["secure"]),
                    "httponly": bool(morsel["httponly"]),
                    "samesite": morsel["samesite"],
                    "domain": morsel["domain"],
                    "path": morsel["path"],
                    "expires": morsel["expires"]
                })

        return {
            "cookies_found": True,
            "cookies": parsed_cookies,
            "error": None
        }