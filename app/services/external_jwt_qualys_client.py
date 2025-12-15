import requests

class QualysClient:
    def __init__(self, base_url: str, jwt: str, timeout_secs: int = 60):
        self.base_url = base_url.rstrip("/")
        self.jwt = jwt
        self.timeout_secs = timeout_secs

    def list_certificates(self, payload: dict) -> requests.Response:
        url = f"{self.base_url}/certview/v1/certificates"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.jwt}",
        }
        return requests.post(url, headers=headers, json=payload, timeout=self.timeout_secs)
