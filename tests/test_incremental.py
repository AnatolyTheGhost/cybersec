
API_URL = "https://example.test/api"
DEFAULT_TIMEOUT = 5


def normalize_username(username: str) -> str:
    return username.strip().lower()


def build_endpoint(username: str) -> str:
    normalized = normalize_username(username)
    return f"{API_URL}/users/{normalized}"


def fetch_user(client, username: str):
    endpoint = build_endpoint(username)
    return client.get(endpoint, timeout=DEFAULT_TIMEOUT)


def format_user(user: dict) -> str:
    name = user.get("name", "unknown")
    email = user.get("email", "unknown")
    return f"{name} <{email}>"


def process_user(client, username: str) -> str:
    user = fetch_user(client, username)
    return format_user(user)


class UserService:
    def __init__(self, client):
        self.client = client

    def get_display_name(self, username: str) -> str:
        user = fetch_user(self.client, username)
        return user.get("name", "unknown")


def run(client, username: str) -> str:
    return process_user(client, username)