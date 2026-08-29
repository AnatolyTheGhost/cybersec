from __future__ import annotations

from models.schemas import AnalysisPack, ScanStartRequest

from .repository_reader import RepositoryFile


class RequestBuilder:
    """Builds scan requests from repository files and pack selection."""

    def build(self, workspace_path: str | object, files: list[RepositoryFile], pack: AnalysisPack | None) -> ScanStartRequest:
        source_code = "\n\n".join(
            f"# {file.relative_path}\n{file.content.rstrip()}"
            for file in files
        )
        return ScanStartRequest(
            workspace_path=str(workspace_path),
            source_code=source_code,
            pack=pack,
        )
