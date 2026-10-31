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

def test_exists_distinguishes_empty_value_from_missing_key() -> None:
    store = KeyValueStore()
    store.set("nickname", "")
    assert store.exists("nickname") is True
    assert store.exists("city") is False

def test_reopening_store_recovers_values_from_log(tmp_path: Path) -> None:
    log_path = tmp_path / "store.log"
    first = KeyValueStore(log_path)
    first.set("city", "Delhi")
    first.set("country", "India")
    first.delete("city")
    recovered = KeyValueStore(log_path)
    assert recovered.get("city") is None
    assert recovered.get("country") == "India"

def test_concurrent_writes_are_not_lost() -> None:
    store = KeyValueStore()
    workers = [Thread(target=store.set, args=(f"key-{number}", str(number))) for number in range(50)]
    for worker in workers: worker.start()
    for worker in workers: worker.join()
    for number in range(50): assert store.get(f"key-{number}") == str(number)

@pytest.mark.parametrize("key", ["", 42, None])
def test_invalid_keys_are_rejected(key: object) -> None:
    with pytest.raises(ValueError):
        KeyValueStore().get(key)  # type: ignore[arg-type]
