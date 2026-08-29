from __future__ import annotations

from models.schemas import AnalysisPack

from .repository_reader import RepositoryReader
from .request_builder import RequestBuilder
from .session import ScanSession
from .session_manager import SessionManager
from .transport import Transport


class ReceiverPipeline:
    """Coordinates repository reading, request building, transport, and session updates."""

    def __init__(
        self,
        repository_reader: RepositoryReader | None = None,
        request_builder: RequestBuilder | None = None,
        transport: Transport | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        self.repository_reader = repository_reader or RepositoryReader()
        self.request_builder = request_builder or RequestBuilder()
        self.transport = transport or Transport()
        self.session_manager = session_manager or SessionManager()

    def run(self, workspace_path: str, pack: AnalysisPack | None) -> ScanSession:
        workspace_string = str(workspace_path)
        session = self.session_manager.create(workspace_path=workspace_string, pack=pack.value if pack is not None else None)
        files = self.repository_reader.read(workspace_string)
        request = self.request_builder.build(workspace_path=workspace_string, files=files, pack=pack)
        try:
            response = self.transport.send(request)
        except RuntimeError as exc:
            return self.session_manager.finish(session, [], status="failed", error=str(exc))

        findings = response.get("findings", [])
        return self.session_manager.finish(session, findings)

    def run_watch(self, workspace_path: str, pack: AnalysisPack | None) -> ScanSession:
        workspace_string = str(workspace_path)
        session = self.session_manager.create(workspace_path=workspace_string, pack=pack.value if pack is not None else None)
        files = self.repository_reader.read(workspace_string)
        
        from .sync.index import FileIndex
        from .sync.manager import SyncManager
        index = FileIndex()
        index.build(files)
        
        request = self.request_builder.build(workspace_path=workspace_string, files=files, pack=pack)
        try:
            response = self.transport.send(request)
        except RuntimeError as exc:
            return self.session_manager.finish(session, [], status="failed", error=str(exc))

        findings = response.get("findings", [])
        session = self.session_manager.finish(session, findings)
        
        print(f"Initial scan complete. Found {session.finding_count} findings.")
        
        manager = SyncManager(workspace_string, session.session_id, self.transport, index)
        manager.start()
        print("Watching for file changes. Press Ctrl+C to stop.")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            manager.stop()
            print("\nStopped watching.")
            
        return session
