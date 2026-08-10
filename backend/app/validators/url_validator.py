from urllib.parse import urlparse
class URLValidator:
    def _normalize(self, url: str) -> str:
         url = url.strip()

         if url.startswith(("http://", "https://")):
             return url

         if "://" in url:
             raise ValueError("Desteklenmeyen URL protokolü.")

         return "https://" + url
       
    def validate(self, url: str) -> str:
        url = self._normalize(url)
        parsed = urlparse(url)
        

        if parsed.scheme not in ("http", "https"):
            raise ValueError("Desteklenmeyen URL protokolü.")
        elif parsed.hostname is None:
            raise ValueError("Geçersiz alan adı.")
        else:
            return url
           
        
