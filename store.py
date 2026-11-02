"""A durable, thread-safe key-value store backed by an append-only log."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock
from uuid import uuid4


class KeyValueStore:
    """Store string values under string keys and optionally persist mutations."""

    def __init__(self, log_path: str | Path | None = None) -> None:
        self._data: dict[str, str] = {}
        self._lock = RLock()
        self._log_path = Path(log_path) if log_path is not None else None
        if self._log_path is not None:
            self._load_log()

    def set(self, key: str, value: str) -> None:
        self._validate_key(key)
        self._validate_value(value)
        with self._lock:
            self._append_record({"operation": "set", "key": key, "value": value})
            self._data[key] = value

    def get(self, key: str) -> str | None:
        self._validate_key(key)
        with self._lock:
            return self._data.get(key)

    def delete(self, key: str) -> bool:
        self._validate_key(key)
        with self._lock:
            if key not in self._data:
                return False
            self._append_record({"operation": "delete", "key": key})
            del self._data[key]
            return True

    def exists(self, key: str) -> bool:
        self._validate_key(key)
        with self._lock:
            return key in self._data

    def compact(self) -> None:
        """Replace the mutation history with the current state atomically."""
        if self._log_path is None:
            return

        with self._lock:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self._log_path.with_name(
                f"{self._log_path.name}.{uuid4().hex}.tmp"
            )
            try:
                with temporary_path.open("w", encoding="utf-8") as log_file:
                    for key, value in self._data.items():
                        record = {"operation": "set", "key": key, "value": value}
                        log_file.write(json.dumps(record) + "\n")
                    log_file.flush()
                    os.fsync(log_file.fileno())
                try:
                    os.replace(temporary_path, self._log_path)
                except PermissionError:
                    # Some restricted Windows filesystems deny replacement of an
                    # existing file. This compatibility path is not crash-atomic.
                    with (
                        temporary_path.open("rb") as source,
                        self._log_path.open("wb") as destination,
                    ):
                        destination.write(source.read())
                        destination.flush()
                        os.fsync(destination.fileno())
            finally:
                if temporary_path.exists():
                    temporary_path.unlink()

    def _load_log(self) -> None:
        assert self._log_path is not None
        if not self._log_path.exists():
            return
        with self._log_path.open("r", encoding="utf-8") as log_file:
            for line_number, line in enumerate(log_file, start=1):
                try:
                    record = json.loads(line)
                    operation = record["operation"]
                    key = record["key"]
                    self._validate_key(key)
                    if operation == "set":
                        value = record["value"]
                        self._validate_value(value)
                        self._data[key] = value
                    elif operation == "delete":
                        self._data.pop(key, None)
                    else:
                        raise ValueError(f"unknown operation {operation!r}")
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    raise ValueError(
                        f"Cannot recover from invalid log record on line {line_number}."
                    ) from error

    def _append_record(self, record: dict[str, str]) -> None:
        if self._log_path is None:
            return
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record) + "\n")
            log_file.flush()
            os.fsync(log_file.fileno())

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not key:
            raise ValueError("key must be a non-empty string")

    @staticmethod
    def _validate_value(value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("value must be a string")
