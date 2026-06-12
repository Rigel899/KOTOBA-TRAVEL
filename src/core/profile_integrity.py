"""
core/profile_integrity.py
Firma HMAC dei profili locali per rilevare modifiche manuali.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import json


class ProfileIntegrity:
    """Firma tamper-evident per i profili locali.

    La chiave applicativa è distribuita insieme al codice, quindi questa
    protezione rileva modifiche manuali accidentali o grossolane ma non va
    trattata come anti-cheat forte contro un utente che controlla la macchina.
    """

    SIGNATURE_FIELD = "_integrity"
    VERSION = "hmac_sha256_v1"
    APP_SECRET = "kotoba_travel_profile_integrity_v1"

    def __init__(self, *, allow_unsigned_profiles: bool = True) -> None:
        self.allow_unsigned_profiles = allow_unsigned_profiles

    @staticmethod
    def _normalize_username(username: str) -> str:
        return (username or "").strip().lower()

    def _key_for(self, username: str) -> bytes:
        seed = f"{self.APP_SECRET}:{self._normalize_username(username)}".encode("utf-8")
        return hashlib.sha256(seed).digest()

    def _canonical_payload(self, data: dict) -> bytes:
        payload = copy.deepcopy(data)
        payload.pop(self.SIGNATURE_FIELD, None)
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    def signature_for(self, username: str, data: dict) -> str:
        return hmac.new(
            self._key_for(username),
            self._canonical_payload(data),
            hashlib.sha256,
        ).hexdigest()

    def signed_profile(self, username: str, data: dict) -> dict:
        payload = copy.deepcopy(data)
        payload.pop(self.SIGNATURE_FIELD, None)
        payload[self.SIGNATURE_FIELD] = {
            "version": self.VERSION,
            "signature": self.signature_for(username, payload),
        }
        return payload

    def verify_profile(self, username: str, data: dict) -> bool:
        integrity = data.get(self.SIGNATURE_FIELD)
        if integrity is None:
            return self.allow_unsigned_profiles
        if not isinstance(integrity, dict):
            return False
        if integrity.get("version") != self.VERSION:
            return False
        signature = integrity.get("signature")
        if not isinstance(signature, str) or not signature:
            return False
        expected = self.signature_for(username, data)
        return hmac.compare_digest(signature, expected)
