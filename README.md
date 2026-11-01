# Key-value store

A small Python key-value store with a thread-safe in-memory index and optional append-only persistence.

## Use it

```python
from store import KeyValueStore

store = KeyValueStore("data/store.log")
store.set("city", "Delhi")
assert store.get("city") == "Delhi"
```

## Run tests

```powershell
python -m pytest
```

## Design

`set` and `delete` append a JSON record to disk, force it to storage, then update the in-memory dictionary. On startup, the store replays those records to recover its latest state.

## V2: log compaction

Call `compact()` to replace old mutation history with a log containing only the current keys. It writes a temporary file and atomically replaces the old log, keeping a crash from leaving a partial active log.

## API and operations

Run `uvicorn api:app --reload`, then use `PUT /v1/keys/{key}` with `{"value":"Delhi"}`. The API runs blocking file operations in `asyncio.to_thread`, allowing concurrent HTTP clients while the core remains simple synchronous Python. `GET /metrics` exposes Prometheus-style request counters.
