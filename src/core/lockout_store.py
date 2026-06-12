"""
core/lockout_store.py
Persistenza del rate limiting per login e recupero password.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from collections.abc import Callable


_log = logging.getLogger("kotoba.lockout")


class LockoutStore:
    MAX_FAILED_ATTEMPTS: int = 5
    LOCKOUT_SECONDS: int = 60   # base del backoff esponenziale
    MAX_LOCKOUT_SECONDS: int = 3600  # tetto massimo: 1 ora

    def __init__(
        self,
        user_data_dir: Callable[[], str],
        normalize_username: Callable[[str], str],
        max_failed_attempts: int | None = None,
        lockout_seconds: int | None = None,
    ) -> None:
        self._user_data_dir = user_data_dir
        self._normalize_username = normalize_username
        self.max_failed_attempts = max_failed_attempts or self.MAX_FAILED_ATTEMPTS
        self.lockout_seconds = lockout_seconds or self.LOCKOUT_SECONDS
        self.max_lockout_seconds = self.MAX_LOCKOUT_SECONDS
        self._lock = threading.Lock()

    def path(self) -> str:
        return os.path.join(self._user_data_dir(), "lockouts.json")

    def read(self) -> dict:
        try:
            with open(self.path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as exc:
            _log.warning("lockouts read failed: invalid json: %s", exc)
            return {}
        except OSError as exc:
            _log.warning("lockouts read failed: %s", exc)
            return {}

    def write(self, data: dict) -> None:
        path = self.path()
        dir_path = os.path.dirname(path)
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(
                prefix=".lockouts.", suffix=".tmp", dir=dir_path, text=True
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            tmp_path = None
        except OSError as exc:
            _log.warning("lockouts write failed: %s", exc)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError as exc:
                    _log.debug("lockouts temp cleanup failed: %s", exc)

    def is_locked_out(self, username: str, context: str = "login") -> tuple[bool, int]:
        username = self._normalize_username(username)
        if not username:
            return False, 0
        key = f"{username}:{context}"
        with self._lock:
            lockouts = self.read()
            entry = lockouts.get(key, {})
            locked_until = entry.get("locked_until")
            if locked_until:
                remaining = locked_until - time.time()
                if remaining > 0:
                    return True, int(remaining) + 1
                entry.pop("locked_until", None)
                entry["attempts"] = 0
                lockouts[key] = entry
                self.write(lockouts)
        return False, 0

    def record_failed_attempt(self, username: str, context: str = "login") -> bool:
        username = self._normalize_username(username)
        if not username:
            return False
        key = f"{username}:{context}"
        with self._lock:
            lockouts = self.read()
            entry = lockouts.setdefault(key, {"attempts": 0})
            locked_until = entry.get("locked_until")
            if locked_until:
                remaining = locked_until - time.time()
                if remaining > 0:
                    return True
                entry.pop("locked_until", None)
                entry["attempts"] = 0
            entry["attempts"] = entry.get("attempts", 0) + 1
            if entry["attempts"] >= self.max_failed_attempts:
                lockout_count = entry.get("lockout_count", 0) + 1
                entry["lockout_count"] = lockout_count
                duration = min(
                    self.lockout_seconds * (2 ** (lockout_count - 1)),
                    self.max_lockout_seconds,
                )
                entry["locked_until"] = time.time() + duration
                entry["attempts"] = 0
                lockouts[key] = entry
                self.write(lockouts)
                return True
            lockouts[key] = entry
            self.write(lockouts)
            return False

    def remaining_attempts(self, username: str, context: str = "login") -> int:
        username = self._normalize_username(username)
        if not username:
            return self.max_failed_attempts
        key = f"{username}:{context}"
        with self._lock:
            lockouts = self.read()
            entry = lockouts.get(key, {})
            locked_until = entry.get("locked_until")
            if locked_until and locked_until > time.time():
                return 0
            return max(0, self.max_failed_attempts - entry.get("attempts", 0))

    def clear_failed_attempts(self, username: str, context: str = "login") -> None:
        username = self._normalize_username(username)
        if not username:
            return
        key = f"{username}:{context}"
        with self._lock:
            lockouts = self.read()
            if key in lockouts:
                del lockouts[key]
                self.write(lockouts)
