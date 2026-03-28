from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time
from uuid import uuid4

from app.config import max_result_points, max_stored_points_total, max_stored_results, result_ttl_seconds
from app.csv_utils import result_to_csv


class ResultStoreError(Exception):
    """Base class for result store lookup failures."""


class ResultNotFound(ResultStoreError):
    """Raised when the result id does not exist."""


class ResultExpired(ResultStoreError):
    """Raised when the result id existed but already expired."""


class ResultTooLarge(ResultStoreError):
    """Raised when a single result is too large to keep in memory."""


@dataclass
class StoredResult:
    freqs: list[float]
    ampl: list[float]
    filename: str
    created_at: float
    point_count: int


class InMemoryResultStore:
    def __init__(self) -> None:
        self._items: dict[str, StoredResult] = {}
        self._expired_ids: set[str] = set()
        self._total_points = 0
        self._lock = Lock()

    def save(self, freqs: list[float], ampl: list[float], *, filename: str) -> str:
        self._purge_expired()
        point_count = len(freqs)
        if point_count > max_result_points():
            raise ResultTooLarge(
                f"Результат слишком большой для временного хранения: максимум {max_result_points()} точек."
            )
        result_id = uuid4().hex
        entry = StoredResult(
            freqs=list(freqs),
            ampl=list(ampl),
            filename=filename,
            created_at=time(),
            point_count=point_count,
        )
        with self._lock:
            self._evict_oldest_until_fit(required_points=point_count)
            self._items[result_id] = entry
            self._expired_ids.discard(result_id)
            self._total_points += point_count
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
                self._remove_item(result_id)

    def stats(self) -> dict[str, int]:
        self._purge_expired()
        with self._lock:
            return {
                "items": len(self._items),
                "total_points": self._total_points,
                "max_results": max_stored_results(),
                "max_points_total": max_stored_points_total(),
                "result_ttl_seconds": result_ttl_seconds(),
            }

    def _evict_oldest_until_fit(self, *, required_points: int) -> None:
        point_cap = max_stored_points_total()
        result_cap = max_stored_results()
        while self._items and (
            len(self._items) >= result_cap or self._total_points + required_points > point_cap
        ):
            oldest_result_id = min(self._items.items(), key=lambda item: item[1].created_at)[0]
            self._remove_item(oldest_result_id)

    def _remove_item(self, result_id: str) -> None:
        entry = self._items.pop(result_id, None)
        if entry is None:
            return
        self._total_points = max(0, self._total_points - entry.point_count)
        self._expired_ids.add(result_id)


result_store = InMemoryResultStore()
