"""
core/profile_store.py
Persistenza dei profili utente locali.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import stat
import tempfile
import threading
import time
from collections.abc import Callable

from src.core.profile_integrity import ProfileIntegrity


_log = logging.getLogger("kotoba.profile")


class ProfileStore:
    def __init__(
        self,
        user_data_dir: Callable[[], str],
        data_dir: Callable[[], str],
        canonical_username_or_raise: Callable[[str], str],
        profile_integrity: ProfileIntegrity | None = None,
    ) -> None:
        self._user_data_dir = user_data_dir
        self._data_dir = data_dir
        self._canonical_username_or_raise = canonical_username_or_raise
        self._profile_integrity = profile_integrity
        self._lock = threading.RLock()
        self._profiles_migrated = False

    @property
    def profiles_migrated(self) -> bool:
        return self._profiles_migrated

    @profiles_migrated.setter
    def profiles_migrated(self, value: bool) -> None:
        self._profiles_migrated = value

    def profiles_dir(self) -> str:
        d = os.path.join(self._user_data_dir(), "profiles")
        os.makedirs(d, exist_ok=True)
        return d

    def legacy_profiles_dir(self) -> str:
        return os.path.join(self._data_dir(), "profiles")

    def migrate_legacy_profiles(self, old_dir: str | None = None) -> None:
        if self._profiles_migrated:
            return
        self._profiles_migrated = True

        if os.environ.get("KOTOBA_MIGRATE_LEGACY_PROFILES") != "1":
            return

        old_dir = old_dir or self.legacy_profiles_dir()
        if not os.path.isdir(old_dir):
            return

        new_dir = self.profiles_dir()
        for filename in os.listdir(old_dir):
            if not (filename.startswith("user_") and filename.endswith(".json")):
                continue
            src = os.path.join(old_dir, filename)
            dst = os.path.join(new_dir, filename)
            if os.path.exists(dst):
                continue
            try:
                shutil.copy2(src, dst)
            except OSError as exc:
                _log.warning("legacy profile migration failed for %s: %s", filename, exc)

    def profile_path(self, username: str) -> str:
        self.migrate_legacy_profiles()
        safe = self._canonical_username_or_raise(username)
        return os.path.join(self.profiles_dir(), f"user_{safe}.json")

    def user_exists(self, username: str) -> bool:
        try:
            return os.path.exists(self.profile_path(username))
        except ValueError:
            return False

    def get_user_data(self, username: str) -> dict | None:
        try:
            path = self.profile_path(username)
        except ValueError:
            return None
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                _log.warning("profile read failed for %s: expected object", username)
                return None
            if self._profile_integrity and not self._profile_integrity.verify_profile(username, data):
                _log.warning("profile integrity check failed for %s", username)
                return None
            return data
        except (json.JSONDecodeError, OSError) as exc:
            _log.warning("profile read failed for %s: %s", username, exc)
            return None

    def _write_user_data_locked(self, username: str, path: str, data: dict) -> None:
        profiles_dir = os.path.dirname(path)
        tmp_path = None
        fd = None
        payload = (
            self._profile_integrity.signed_profile(username, data)
            if self._profile_integrity
            else data
        )

        def write_payload(f) -> None:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())

        with self._lock:
            try:
                fd, tmp_path = tempfile.mkstemp(
                    prefix=f".{os.path.basename(path)}.",
                    suffix=".tmp",
                    dir=profiles_dir,
                    text=True,
                )
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    fd = None
                    write_payload(f)

                for attempt in range(6):
                    try:
                        if os.path.exists(path):
                            try:
                                os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
                            except OSError as exc:
                                _log.debug("profile chmod before replace failed for %s: %s", username, exc)
                        os.replace(tmp_path, path)
                        return
                    except PermissionError:
                        if attempt == 5:
                            break
                        time.sleep(0.05 * (attempt + 1))

                with open(path, "w", encoding="utf-8") as f:
                    write_payload(f)
            finally:
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError as exc:
                        _log.debug("profile temp fd close failed for %s: %s", username, exc)
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError as exc:
                        _log.debug("profile temp cleanup failed for %s: %s", username, exc)

    def create_user_data(self, username: str, data: dict) -> None:
        path = self.profile_path(username)
        with self._lock:
            if os.path.exists(path):
                raise ValueError(f"Il nome utente '{username}' è già in uso.")
            self._write_user_data_locked(username, path, data)

    def update_user_data(self, username: str, data: dict) -> None:
        path = self.profile_path(username)
        with self._lock:
            self._write_user_data_locked(username, path, data)

    def delete_account(self, username: str) -> None:
        try:
            path = self.profile_path(username)
        except ValueError:
            return
        with self._lock:
            if os.path.exists(path):
                os.remove(path)
