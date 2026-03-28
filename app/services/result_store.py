from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time
from uuid import uuid4

from app.config import result_ttl_seconds
from app.csv_utils import result_to_csv


class ResultStoreError(Exception):
    """Base class for result store lookup failures."""


class ResultNotFound(ResultStoreError):
    """Raised when the result id does not exist."""


class ResultExpired(ResultStoreError):
    """Raised when the result id existed but already expired."""


@dataclass
class StoredResult:
    freqs: list[float]
    ampl: list[float]
    filename: str
    created_at: float


class InMemoryResultStore:
    def __init__(self) -> None:
        self._items: dict[str, StoredResult] = {}
        self._expired_ids: set[str] = set()
        self._lock = Lock()

    def save(self, freqs: list[float], ampl: list[float], *, filename: str) -> str:
        self._purge_expired()
        result_id = uuid4().hex
        entry = StoredResult(
            freqs=list(freqs),
            ampl=list(ampl),
            filename=filename,
            created_at=time(),
        )
        with self._lock:
            self._items[result_id] = entry
            self._expired_ids.discard(result_id)
        return result_id

    def get_csv(self, result_id: str) -> tuple[str, str]:
        self._purge_expired()
        with self._lock:
            entry = self._items.get(result_id)
            if entry is None:
                if result_id in self._expired_ids:
                    self._expired_ids.discard(result_id)
                    raise ResultExpired("Результат устарел. Выполните расчёт заново.")
                raise ResultNotFound("Результат не найден.")
            return entry.filename, result_to_csv(entry.freqs, entry.ampl)

    def _purge_expired(self) -> None:
        ttl = result_ttl_seconds()
        now = time()
        expired: list[str] = []
        with self._lock:
            for result_id, entry in self._items.items():
                if now - entry.created_at > ttl:
                    expired.append(result_id)
            for result_id in expired:
                self._items.pop(result_id, None)
                self._expired_ids.add(result_id)


result_store = InMemoryResultStore()
