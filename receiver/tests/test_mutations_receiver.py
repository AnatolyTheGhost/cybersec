from __future__ import annotations

from datetime import datetime, timezone

from mutations_receiver import (
    AdapterRegistry,
    ClaudeCodeAdapter,
    FileWatcherAdapter,
    MutationEvent,
    MutationsReceiver,
    VSCodeAdapter,
)


def test_adapter_registration_and_registry_lookup():
    registry = AdapterRegistry()
    adapter = VSCodeAdapter(name="vscode")

    registry.register(adapter)

    assert registry.get("vscode") is adapter
    assert "vscode" in registry.names


def test_receiver_forwards_valid_events_to_consumer():
    receiver = MutationsReceiver()
    received: list[MutationEvent] = []
    receiver.add_consumer(received.append)

    adapter = VSCodeAdapter(name="vscode")
    receiver.register_adapter(adapter)
    receiver.start()

    event = MutationEvent(
        event_type="FileOpened",
        timestamp=datetime.now(timezone.utc),
        session_id="session-1",
        source_adapter="vscode",
        file_path="/tmp/main.py",
        payload={"kind": "editor"},
    )
    adapter.emit(event)

    receiver.stop()

    assert len(received) == 1
    assert received[0].event_type == "FileOpened"
    assert received[0].file_path == "/tmp/main.py"


def test_receiver_rejects_invalid_events():
    receiver = MutationsReceiver()
    received: list[MutationEvent] = []
    receiver.add_consumer(received.append)

    adapter = FileWatcherAdapter(name="filewatcher")
    receiver.register_adapter(adapter)
    receiver.start()

    invalid_event = MutationEvent(
        event_type="",
        timestamp=datetime.now(timezone.utc),
        session_id="",
        source_adapter="",
        file_path=None,
        payload={},
    )

    assert receiver.handle_event(invalid_event) is False
    assert received == []

    receiver.stop()


def test_multiple_adapters_work_simultaneously():
    receiver = MutationsReceiver()
    received: list[MutationEvent] = []
    receiver.add_consumer(received.append)

    vscode = VSCodeAdapter(name="vscode")
    watcher = FileWatcherAdapter(name="filewatcher")
    claude = ClaudeCodeAdapter(name="claude")

    receiver.register_adapter(vscode)
    receiver.register_adapter(watcher)
    receiver.register_adapter(claude)
    receiver.start()

    vscode.emit_test_event("TextDocumentChanged", file_path="/tmp/app.py")
    watcher.emit_test_event("FileSaved", file_path="/tmp/app.py")
    claude.emit_test_event("SessionStarted", file_path=None)

    receiver.stop()

    assert [event.source_adapter for event in received] == ["vscode", "filewatcher", "claude"]
    assert [event.event_type for event in received] == ["TextDocumentChanged", "FileSaved", "SessionStarted"]


def test_mutations_receiver_scan_and_change_detection(tmp_path):
    from unittest.mock import MagicMock
    from mutations_receiver import BackendClient, FileWatcherAdapter

    # Create dummy files
    workspace = tmp_path / "my_project"
    workspace.mkdir()
    file1 = workspace / "file1.py"
    file1.write_text("print('hello')", encoding="utf-8")
    
    file2 = workspace / "file2.py"
    file2.write_text("print('world')", encoding="utf-8")

    # Stub the backend client
    mock_backend = MagicMock(spec=BackendClient)

    receiver = MutationsReceiver(backend_client=mock_backend)
    receiver.connect_backend("my-workspace", str(workspace))
    
    # Run scan
    receiver.scan_project()
    
    # Assert hashes are cached
    file1_path = str(file1.resolve())
    file2_path = str(file2.resolve())
    assert file1_path in receiver._file_hashes
    assert file2_path in receiver._file_hashes
    
    hash1 = receiver._file_hashes[file1_path]
    
    # Now simulate receiving a FileSaved event for file1 with NO changes
    mock_backend.submit_mutations.reset_mock()
    adapter = FileWatcherAdapter()
    receiver.register_adapter(adapter)
    receiver.start()
    
    adapter.emit_test_event("FileSaved", file_path=file1_path)
    
    # Submit should not have been called because hash has not changed
    mock_backend.submit_mutations.assert_not_called()
    
    # Now modify file1
    file1.write_text("print('hello modified')", encoding="utf-8")
    
    adapter.emit_test_event("FileSaved", file_path=file1_path)
    
    # Submit SHOULD be called
    mock_backend.submit_mutations.assert_called_once()
    assert receiver._file_hashes[file1_path] != hash1
    
    # Let's clean up
    receiver.stop()
