"""
core/validators.py
Validazione credenziali e normalizzazione username.
"""
from __future__ import annotations


class CredentialValidator:
    PASSWORD_MIN_LENGTH = 8
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 24
    USERNAME_ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_")

    @staticmethod
    def normalize_username(username: str) -> str:
        return (username or "").strip().lower()

    @classmethod
    def username_validation_error(cls, username: str) -> str | None:
        normalized = cls.normalize_username(username)
        if not normalized:
            return "Inserisci un nome utente."
        if len(normalized) < cls.USERNAME_MIN_LENGTH:
            return f"Il nome utente deve avere almeno {cls.USERNAME_MIN_LENGTH} caratteri."
        if len(normalized) > cls.USERNAME_MAX_LENGTH:
            return f"Il nome utente deve avere al massimo {cls.USERNAME_MAX_LENGTH} caratteri."
        if any(ch not in cls.USERNAME_ALLOWED_CHARS for ch in normalized):
            return "Usa solo lettere, numeri o underscore nel nome utente."
        return None

    @classmethod
    def is_valid_username(cls, username: str) -> bool:
        return cls.username_validation_error(username) is None

    @classmethod
    def canonical_username_or_raise(cls, username: str) -> str:
        error = cls.username_validation_error(username)
        if error:
            raise ValueError(error)
        return cls.normalize_username(username)

    @classmethod
    def password_validation_error(cls, password: str) -> str | None:
        if not password:
            return "Inserisci una password."
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return f"La password deve essere di almeno {cls.PASSWORD_MIN_LENGTH} caratteri."
        return None
