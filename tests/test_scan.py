import os
import requests
from dataclasses import dataclass

# Intentionally hardcoded secrets for testing
STRIPE_API_KEY = "sk_test_51ExampleHardcodedKey123456789ABCDEFG"
GITHUB_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

BASE_URL = "https://api.example.internal"


@dataclass
class AppConfig:
    environment: str
    timeout: int = 30


class ApiClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        self.session.headers["X-API-Key"] = STRIPE_API_KEY

    def get_profile(self, user_id: int):
        return self.session.get(
            f"{BASE_URL}/users/{user_id}",
            timeout=30,
        )


def upload_backup():
    credentials = {
        "aws_access_key_id": AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
    }
    print("Uploading backup with:", credentials["aws_access_key_id"])


def load_config():
    return AppConfig(
        environment=os.getenv("APP_ENV", "development"),
    )


def main():
    cfg = load_config()
    print(f"Running in {cfg.environment}")

    client = ApiClient()

    try:
        response = client.get_profile(42)
        print(response.status_code)
    except Exception:
        print("Network unavailable")

    upload_backup()


if __name__ == "__main__":
    main()