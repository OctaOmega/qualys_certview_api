import time
import threading
import requests

class QualysClient:
    """
    - Fetch token from QUALYS_AUTH_URL using form-urlencoded body
    - Cache token for 4 hours (or slightly less as safety buffer)
    """

    def __init__(self, base_url: str, auth_url: str, username: str, password: str, timeout_secs: int = 60):
        self.base_url = base_url.rstrip("/")
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.timeout_secs = timeout_secs

        self._lock = threading.Lock()
        self._token: str | None = None
        self._token_expires_at: float = 0.0  # epoch seconds

        # Token validity stated as 4 hours; use buffer to avoid edge expiry.
        self._token_ttl_seconds = 4 * 60 * 60
        self._refresh_buffer_seconds = 60  # refresh 1 min early

    def _is_token_valid(self) -> bool:
        return bool(self._token) and time.time() < (self._token_expires_at - self._refresh_buffer_seconds)

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Returns a valid token, fetching a new one only if needed.
        """
        with self._lock:
            if not force_refresh and self._is_token_valid():
                return self._token  # type: ignore

            if not self.username or not self.password:
                raise ValueError("QUALYS_USERNAME / QUALYS_PASSWORD not set")

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "username": self.username,
                "password": self.password,
                "token": "true",
                "permissions": "true",
            }

            resp = requests.post(self.auth_url, headers=headers, data=data, timeout=self.timeout_secs)
            if resp.status_code != 200:
                raise RuntimeError(f"Qualys auth failed ({resp.status_code}): {resp.text[:2000]}")

            # Qualys auth responses can vary by tenant; try common shapes.
            body = resp.json() if "application/json" in resp.headers.get("Content-Type", "") else {}

            token = (
                body.get("token")
                or body.get("access_token")
                or body.get("jwt")
                or body.get("data", {}).get("token")
            )

            if not token:
                # If JSON parsing didn't find it, fall back to text (some gateways return token as plain string)
                text = resp.text.strip()
                # only accept if it looks like a JWT (3 dot-separated parts)
                if text.count(".") == 2 and len(text) > 50:
                    token = text

            if not token:
                raise RuntimeError(f"Could not parse token from auth response: {resp.text[:2000]}")

            self._token = token
            self._token_expires_at = time.time() + self._token_ttl_seconds
            return self._token

    def _auth_headers(self) -> dict:
        token = self.get_token()
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def list_certificates(self, payload: dict) -> requests.Response:
        url = f"{self.base_url}/certview/v1/certificates"
        return requests.post(url, headers=self._auth_headers(), json=payload, timeout=self.timeout_secs)
