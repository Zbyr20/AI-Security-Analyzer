import socket
import ssl
from urllib.parse import urlparse #hostname'i almak için
class SSLScanner:

    def scan(self, url: str):
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname is None:
            raise ValueError("Geçersiz hostname")
        try:
            ssl_socket = self._connect(hostname)
            certificate = self._get_certificate(ssl_socket)
            result = self._build_result(certificate)
            ssl_socket.close()
            return result
        except (socket.timeout, socket.gaierror, ssl.SSLError, OSError) as e:
            return { 
                "ssl_valid": False,
                "certificate": None,
                "error": str(e)
            }
    
    
    def _connect(self, hostname):
        context = ssl.create_default_context()
        sock = socket.create_connection(
             
                (hostname, 443),
                timeout = 5
             
        )
        ssl_socket = context.wrap_socket(
            sock,
            server_hostname= hostname
        )
        return ssl_socket
       
       
    def _get_certificate(self, ssl_socket):
        return ssl_socket.getpeercert()
    def _build_result(self, certificate):
        return {
            "ssl_valid" : bool(certificate),
            "certificate" : certificate
        }