# Mutations Receiver

This package provides the initial event-ingestion layer for mutation events. It is intentionally independent from any specific editor or IDE and focuses on a modular adapter architecture.

## Architecture

- MutationsReceiver: owns lifecycle management, validation, and forwarding.
- MutationAdapter: abstract interface implemented by adapters.
- MutationEvent: shared event protocol with metadata and extensible payloads.
- AdapterRegistry: dynamic registration mechanism for loading adapters.

## Adding a new adapter

1. Create a subclass of MutationAdapter.
2. Implement emit_test_event to emit normalized MutationEvent values.
3. Register the adapter with MutationsReceiver via register_adapter.

The receiver only talks to adapters through the MutationAdapter interface, which keeps the core module free from IDE-specific logic.

## Current stub adapters

- VSCodeAdapter
- FileWatcherAdapter
- ClaudeCodeAdapter

These adapters are placeholders and emit mocked events for now.
