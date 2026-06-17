"""
core/auth_service.py
Autenticazione locale, creazione account ed export sicuro profilo.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from src.core.profile_factory import build_default_profile


class AuthService:
    SENSITIVE_EXPORT_FIELDS = {"password_hash", "recovery_answer_hash", "_integrity"}
    EXPORT_NOTE = "Hash di sicurezza non inclusi. Solo dati di progresso."

    def __init__(
        self,
        normalize_username: Callable[[str], str],
        canonical_username_or_raise: Callable[[str], str],
        password_validation_error: Callable[[str], str | None],
        hash_string: Callable[[str], str],
        verify_secret: Callable[[str, str], bool],
        is_legacy_hash: Callable[[str, str], bool],
        get_user_data: Callable[[str], dict | None],
        update_user_data: Callable[[str, dict], None],
        create_user_data: Callable[[str, dict], None],
        prepare_profiles: Callable[[], None] | None = None,
    ) -> None:
        self._normalize_username = normalize_username
        self._canonical_username_or_raise = canonical_username_or_raise
        self._password_validation_error = password_validation_error
        self._hash_string = hash_string
        self._verify_secret = verify_secret
        self._is_legacy_hash = is_legacy_hash
        self._get_user_data = get_user_data
        self._update_user_data = update_user_data
        self._create_user_data = create_user_data
        self._prepare_profiles = prepare_profiles or (lambda: None)

    def verify_login(self, username: str, password: str) -> bool:
        username = self._normalize_username(username)
        data = self._get_user_data(username)
        if not data:
            return False

        stored_hash = data.get("password_hash", "")
        if not self._verify_secret(password, stored_hash):
            return False

        if self._is_legacy_hash(password, stored_hash):
            data["password_hash"] = self._hash_string(password)
            self._update_user_data(username, data)
        return True

    def create_account(self, username: str, password: str, question: str, answer: str) -> None:
        username = self._canonical_username_or_raise(username)
        password_error = self._password_validation_error(password)
        if password_error:
            raise ValueError(password_error)

        data = build_default_profile(
            username,
            self._hash_string(password),
            question,
            self._hash_string(answer),
        )
        self._prepare_profiles()
        self._create_user_data(username, data)

    def export_safe_profile(self, username: str) -> dict | None:
        data = self._get_user_data(username)
        if not data:
            return None

        safe = {k: v for k, v in data.items() if k not in self.SENSITIVE_EXPORT_FIELDS}
        safe["_export_note"] = self.EXPORT_NOTE
        safe["_exported_at"] = datetime.now().isoformat()
        return safe
