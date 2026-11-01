# Notes

## Design decisions

- A Python dictionary provides O(1) average-time reads by key.
- Each mutation is written as JSON Lines before the dictionary changes. A crash cannot leave memory ahead of the durable log.
- The log is replayed in order at startup; later records replace earlier state.
- An `RLock` holds each operation together, preventing concurrent threads from interleaving a log write and a dictionary update.
- Empty values are valid. Empty keys are rejected.
- `compact()` writes the current state to a unique temporary file, flushes it to storage, and uses `os.replace()` to install it. Readers see either the old complete log or the new complete log on normal filesystems.
- Some restricted Windows filesystems deny replacement of an existing file. A compatibility fallback deletes the old log first; it works but loses crash atomicity, which is a known limitation to explain rather than hide.

## Interview prompts

- Why use an append-only log? Writes are simple and recovery replays ordered events.
- What is the tradeoff? The log grows indefinitely; the next improvement is compaction, which writes a snapshot then safely replaces old history.
- Why call `fsync`? Flushing Python's buffer alone does not require the operating system to persist the change to storage.
- Why write a temporary file before compaction? Rewriting the active log directly could leave it empty or partial after a crash.

## Failure cases covered

- Missing keys
- Replacing values
- Deleting a missing key
- Restart recovery
- Invalid keys and values
- Malformed log records
- Concurrent writes
- Log growth through compaction
