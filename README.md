# Key-Value Store

A durable Python key-value store with an in-memory dictionary, append-only JSON Lines logging, restart recovery, thread safety, and log compaction.

## Features

- Average O(1) reads and writes through a Python dictionary
- Durable append-only mutation log
- Startup recovery by replaying persisted operations
- Thread safety with RLock
- Log compaction to control storage growth
- Tests for recovery, deletion, invalid input, and concurrent writes

## Architecture

Client -> KeyValueStore -> dictionary, lock, and log file.

For a write, the store validates input, acquires the lock, appends a log record, updates memory, and releases the lock. On startup, it replays every log record to rebuild current state.

## Requirements

- Python 3.11+
- pytest for tests

## Setup

Clone the repository, create a virtual environment, and install pytest.

```powershell
python -m pip install pytest
python -m pytest
```

## Usage

```python
from store import KeyValueStore

store = KeyValueStore('data/store.log')
store.set('city', 'Delhi')
print(store.get('city'))
```

## Persistence and recovery

Each mutation is stored as a JSON line. When the process restarts, the store replays those records in order. Later operations replace earlier state for the same key.

## Compaction

Logs grow with every mutation. Call compact() to rewrite the log with only current keys. The implementation writes a temporary replacement first before attempting to install it.

## Tradeoffs

JSON Lines is readable and simple, but a binary format would use less storage. RLock protects threads in one process; it does not coordinate separate processes using the same log file.

## License

MIT License.
