import ssl
import socket
from datetime import datetime, timezone

def get_ssl_expiry_date(hostname: str) -> datetime:
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_str = cert['notAfter']
                expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                return expiry_date.replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"Issues at {hostname}: {e}")
        return None