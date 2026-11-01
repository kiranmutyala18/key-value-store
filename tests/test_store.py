from pathlib import Path
from threading import Thread

import pytest

from store import KeyValueStore


def test_set_then_get() -> None:
    store = KeyValueStore()
    store.set("city", "Delhi")
    assert store.get("city") == "Delhi"


def test_unknown_key_returns_none() -> None:
    assert KeyValueStore().get("country") is None


def test_set_replaces_an_existing_value() -> None:
    store = KeyValueStore()
    store.set("city", "Delhi")
    store.set("city", "Mumbai")
    assert store.get("city") == "Mumbai"


def test_delete_removes_an_existing_key() -> None:
    store = KeyValueStore()
    store.set("city", "Delhi")
    assert store.delete("city") is True
    assert store.get("city") is None


def test_delete_reports_a_missing_key() -> None:
    assert KeyValueStore().delete("city") is False


def test_exists_distinguishes_empty_value_from_missing_key() -> None:
    store = KeyValueStore()
    store.set("nickname", "")
    assert store.exists("nickname") is True
    assert store.exists("city") is False


def test_reopening_store_recovers_values_from_log(tmp_path: Path) -> None:
    log_path = tmp_path / "store.log"
    first_store = KeyValueStore(log_path)
    first_store.set("city", "Delhi")
    first_store.set("country", "India")
    first_store.delete("city")
    recovered_store = KeyValueStore(log_path)
    assert recovered_store.get("city") is None
    assert recovered_store.get("country") == "India"


def test_compaction_keeps_current_state_and_reduces_history(tmp_path: Path) -> None:
    log_path = tmp_path / "store.log"
    store = KeyValueStore(log_path)
    store.set("city", "Delhi")
    store.set("city", "Mumbai")
    store.set("country", "India")
    store.delete("city")

    store.compact()

    assert log_path.read_text(encoding="utf-8").count("\n") == 1
    recovered_store = KeyValueStore(log_path)
    assert recovered_store.get("city") is None
    assert recovered_store.get("country") == "India"


def test_concurrent_writes_are_not_lost() -> None:
    store = KeyValueStore()
    workers = [
        Thread(target=store.set, args=(f"key-{number}", str(number)))
        for number in range(50)
    ]

    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    for number in range(50):
        assert store.get(f"key-{number}") == str(number)


@pytest.mark.parametrize("key", ["", 42, None])
def test_invalid_keys_are_rejected(key: object) -> None:
    with pytest.raises(ValueError, match="key must be a non-empty string"):
        KeyValueStore().get(key)  # type: ignore[arg-type]


def test_invalid_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="value must be a string"):
        KeyValueStore().set("count", 3)  # type: ignore[arg-type]
