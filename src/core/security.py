"""
core/security.py
Hashing e verifica dei segreti locali dell'app.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets


class PasswordHasher:
    LEGACY_HASH_SALT = "kotoba_travel_local_v2"
    PBKDF2_ITERATIONS = 210_000

    @staticmethod
    def hash_string(text: str, iterations: int = PBKDF2_ITERATIONS) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            text.encode(),
            salt.encode(),
            iterations,
        ).hex()
        return f"pbkdf2_sha256${iterations}${salt}${digest}"

    @staticmethod
    def hash_v1(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    @staticmethod
    def hash_fixed_salt(text: str, legacy_salt: str = LEGACY_HASH_SALT) -> str:
        payload = f"{legacy_salt}:{text}".encode()
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def verify_pbkdf2(text: str, stored_hash: str) -> bool:
        try:
            algo, iterations_raw, salt, expected = stored_hash.split("$", 3)
            iterations = int(iterations_raw)
        except (ValueError, TypeError):
            return False
        if algo != "pbkdf2_sha256" or iterations < 1 or not salt or not expected:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            text.encode(),
            salt.encode(),
            iterations,
        ).hex()
        return hmac.compare_digest(expected, digest)

    @staticmethod
    def verify_secret(text: str, stored_hash: str, legacy_salt: str = LEGACY_HASH_SALT) -> bool:
        if not stored_hash:
            return False
        if stored_hash.startswith("pbkdf2_sha256$"):
            return PasswordHasher.verify_pbkdf2(text, stored_hash)
        return (
            hmac.compare_digest(stored_hash, PasswordHasher.hash_fixed_salt(text, legacy_salt))
            or hmac.compare_digest(stored_hash, PasswordHasher.hash_v1(text))
        )

    @staticmethod
    def is_legacy_hash(text: str, stored_hash: str, legacy_salt: str = LEGACY_HASH_SALT) -> bool:
        return (
            bool(stored_hash)
            and not stored_hash.startswith("pbkdf2_sha256$")
            and PasswordHasher.verify_secret(text, stored_hash, legacy_salt)
        )
