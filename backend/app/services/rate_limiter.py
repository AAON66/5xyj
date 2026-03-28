from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class _FailureRecord:
    count: int = 0
    locked_until: float = 0.0


class RateLimiter:
    """In-memory rate limiter keyed by arbitrary string (e.g. employee_id).

    After *max_failures* consecutive failures for a key, the key is locked
    for *lockout_seconds*.  A successful verification should call ``reset``
    to clear the failure counter.
    """

    def __init__(self, max_failures: int = 5, lockout_seconds: int = 900) -> None:
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        self._records: dict[str, _FailureRecord] = {}
        self._lock = threading.Lock()

    def is_locked(self, key: str) -> bool:
        with self._lock:
            record = self._records.get(key)
            if record is None:
                return False
            if record.locked_until and time.monotonic() < record.locked_until:
                return True
            if record.locked_until and time.monotonic() >= record.locked_until:
                # Lockout expired -- reset
                del self._records[key]
                return False
            return False

    def record_failure(self, key: str) -> bool:
        """Record a failed attempt.  Returns True if the key is now locked."""
        with self._lock:
            record = self._records.get(key)
            if record is None:
                record = _FailureRecord()
                self._records[key] = record
            # If currently locked, stay locked
            if record.locked_until and time.monotonic() < record.locked_until:
                return True
            record.count += 1
            if record.count >= self.max_failures:
                record.locked_until = time.monotonic() + self.lockout_seconds
                return True
            return False

    def reset(self, key: str) -> None:
        with self._lock:
            self._records.pop(key, None)
