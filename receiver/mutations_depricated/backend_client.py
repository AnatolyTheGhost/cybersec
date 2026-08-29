from __future__ import annotations

import json
from typing import Any
from urllib import error, request


class BackendClient:
    """Minimal HTTP client for the backend transport layer."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self._base_url = base_url.rstrip("/")

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def start_analysis(self, workspace_id: str, workspace_path: str, goals: list[str]) -> dict[str, Any]:
        payload = {
            "workspace_id": workspace_id,
            "workspace_path": workspace_path,
            "goals": goals,
        }
        return self._request("POST", "/start", payload)

    def submit_mutations(self, workspace_id: str, mutations: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "workspace_id": workspace_id,
            "mutations": mutations,
        }
        return self._request("POST", "/mutations", payload)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(self._base_url + path, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=5) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            raise RuntimeError(f"Backend request failed with {exc.code}: {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Backend request failed: {exc.reason}") from exc
