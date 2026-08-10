from urllib.request import Request, urlopen

class HeaderScanner:

    SECURITY_HEADERS = {
        "content-security-policy": "csp",
        "strict-transport-security": "hsts",
        "x-frame-options": "x_frame_options",
        "x-content-type-options": "x_content_type_options",
        "referrer-policy": "referrer_policy",
        "permissions-policy": "permissions_policy"
    }
    def scan(self,url:str) -> dict:
        try:
            request = Request( 
                url,
                method= "GET",
                headers= {
                    "User-Agent": "AI-Security-Analyzer/1.0"
                }
            )
            with urlopen(request, timeout=10) as response:
                headers = response.headers
            return self._build_result(headers)

        except Exception as e:
            return {
                "error" : str(e)
            }

    def _build_result(self, headers) ->dict:
        result = {
            "error": None
        }
        header_names= {
            key.lower()
            for key in headers.keys()
        }
        for header_name, result_name in self.SECURITY_HEADERS.items():
            result[result_name] = header_name in header_names
        return result
        
    