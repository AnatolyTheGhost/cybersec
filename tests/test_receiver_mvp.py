from __future__ import annotations

from pathlib import Path

from models.schemas import AnalysisPack

from receiver.engine_receiver.pipeline import ReceiverPipeline
from receiver.engine_receiver.repository_reader import RepositoryFile, RepositoryReader
from receiver.engine_receiver.request_builder import RequestBuilder
from receiver.engine_receiver.session import ScanSession


class FakeTransport:
    def __init__(self, payload=None) -> None:
        self.payload = payload or {
            "status": "completed",
            "findings": [{"rule_id": "demo-rule", "message": "demo finding"}],
        }
        self.requests = []

    def send(self, request):
        self.requests.append(request)
        return self.payload


def _write_repo(root: Path) -> None:
    (root / ".git").mkdir(parents=True)
    (root / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    (root / "src").mkdir(parents=True)
    (root / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (root / "node_modules").mkdir(parents=True)
    (root / "node_modules" / "pkg").mkdir(parents=True)
    (root / "node_modules" / "pkg" / "index.js").write_text("console.log('skip')\n", encoding="utf-8")
    (root / "__pycache__").mkdir(parents=True)
    (root / "__pycache__" / "module.pyc").write_bytes(b"compiled")


def test_repository_reader_collects_relative_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_repo(repo_root)

    files = RepositoryReader().read(repo_root)

    paths = [item.relative_path for item in files]

    assert paths == ["src/app.py"]


def test_request_builder_serializes_relative_paths() -> None:
    files = [RepositoryFile(relative_path="src/app.py", content="print('hello')\n")]

    request = RequestBuilder().build(workspace_path=".", files=files, pack=AnalysisPack.SECRETS)

    assert request.workspace_path == "."
    assert request.pack == AnalysisPack.SECRETS
    assert "src/app.py" in request.source_code
    assert "print('hello')" in request.source_code


def test_receiver_pipeline_stores_findings_and_finishes_session(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    _write_repo(repo_root)

    transport = FakeTransport()
    pipeline = ReceiverPipeline(
        repository_reader=RepositoryReader(),
        request_builder=RequestBuilder(),
        transport=transport,
    )

    session = pipeline.run(workspace_path=repo_root, pack=AnalysisPack.SECRETS)

    assert isinstance(session, ScanSession)
    assert session.status == "completed"
    assert session.finding_count == 1
    assert session.findings[0]["rule_id"] == "demo-rule"
    assert transport.requests[0].workspace_path == str(repo_root)
