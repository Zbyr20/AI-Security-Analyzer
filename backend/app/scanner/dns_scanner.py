import dns.resolver
from urllib.parse import urlparse


class DNSScanner:

    RECORD_TYPES = ["A", "AAAA", "MX", "NS", "CNAME"]

    def scan(self, url: str) -> dict:

        hostname = urlparse(url).hostname

        if not hostname:
            return {
                "error": "Geçersiz hostname."
            }

        result = {
            "domain": hostname,
            "a": [],
            "aaaa": [],
            "mx": [],
            "ns": [],
            "cname": [],
            "error": None
        }

        for record_type in self.RECORD_TYPES:

            try:
                answers = dns.resolver.resolve(
                    hostname,
                    record_type
                )

                key = record_type.lower()

                result[key] = [
                    answer.to_text()
                    for answer in answers
                ]

            except (
                dns.resolver.NoAnswer,
                dns.resolver.NXDOMAIN,
                dns.resolver.NoNameservers
            ):
                pass

            except Exception as e:
                result["error"] = str(e)

        return result