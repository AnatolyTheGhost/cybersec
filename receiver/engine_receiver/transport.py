from __future__ import annotations

import json
import time
from typing import Any
from urllib import error, request as urllib_request

from models.schemas import ScanStartRequest


class Transport:
    """Dedicated HTTP transport for scan requests."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 5.0, max_retries: int = 2) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def send(self, request: ScanStartRequest) -> dict[str, Any]:
        payload = {
            "workspace_path": request.workspace_path,
            "source_code": request.source_code,
            "pack": request.pack.value if request.pack is not None else None,
        }
        data = json.dumps(payload).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            req = urllib_request.Request(
                self.base_url + "/scan",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib_request.urlopen(req, timeout=self.timeout) as response:
                    body = response.read().decode("utf-8")
                    return json.loads(body) if body else {}
            except error.HTTPError as exc:
                body = exc.read().decode("utf-8")
                last_error = RuntimeError(f"Scan request failed with {exc.code}: {body}")
            except error.URLError as exc:
                last_error = RuntimeError(f"Scan request failed: {exc.reason}")
            except TimeoutError as exc:
                last_error = RuntimeError(f"Scan request timed out after {self.timeout} seconds")

            if attempt < self.max_retries - 1:
                time.sleep(0.2 * (attempt + 1))

        if last_error is not None:
            raise last_error
        raise RuntimeError("Scan request failed without a captured error")

    def send_file_changes(self, session_id: str, changes: list[dict[str, Any]]) -> None:
        payload = {
            "session_id": session_id,
            "changes": changes,
        }
        data = json.dumps(payload).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            req = urllib_request.Request(
                self.base_url + "/sync",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib_request.urlopen(req, timeout=self.timeout) as response:
                    return
            except error.HTTPError as exc:
                body = exc.read().decode("utf-8")
                last_error = RuntimeError(f"Sync request failed with {exc.code}: {body}")
            except error.URLError as exc:
                last_error = RuntimeError(f"Sync request failed: {exc.reason}")
            except TimeoutError as exc:
                last_error = RuntimeError(f"Sync request timed out after {self.timeout} seconds")

            if attempt < self.max_retries - 1:
                time.sleep(0.2 * (attempt + 1))

        if last_error is not None:
            raise last_error
        raise RuntimeError("Sync request failed without a captured error")
