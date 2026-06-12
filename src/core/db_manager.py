"""
core/db_manager.py
Gestione persistenza utenti, punteggi e achievement.
I dati statici sono salvati in asset/data.
I profili utente scrivibili sono salvati fuori da asset, nella cartella utente.
"""

from src.core.app_paths import AppPaths
from src.core.auth_service import AuthService
from src.core.content_store import ContentStore
from src.core.lockout_store import LockoutStore
from src.core.profile_integrity import ProfileIntegrity
from src.core.profile_store import ProfileStore
from src.core.progress_service import ProgressService
from src.core.security import PasswordHasher
from src.core.validators import CredentialValidator


class DBManager:
    current_username: str = "Viandante"
    LEGACY_HASH_SALT = PasswordHasher.LEGACY_HASH_SALT
    PBKDF2_ITERATIONS = PasswordHasher.PBKDF2_ITERATIONS
    PASSWORD_MIN_LENGTH = CredentialValidator.PASSWORD_MIN_LENGTH
    USERNAME_MIN_LENGTH = CredentialValidator.USERNAME_MIN_LENGTH
    USERNAME_MAX_LENGTH = CredentialValidator.USERNAME_MAX_LENGTH
    USERNAME_ALLOWED_CHARS = CredentialValidator.USERNAME_ALLOWED_CHARS
    _json_cache: dict[str, tuple[int, object]] = {}
    _JSON_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = ContentStore.REQUIRED_FIELDS
    _profiles_migrated = False
    MAX_FAILED_ATTEMPTS: int = LockoutStore.MAX_FAILED_ATTEMPTS
    LOCKOUT_SECONDS: int = LockoutStore.LOCKOUT_SECONDS
    _content_store: ContentStore | None = None
    _lockout_store: LockoutStore | None = None
    _profile_store: ProfileStore | None = None
    _progress_service: ProgressService | None = None
    _auth_service: AuthService | None = None
    _profile_integrity: ProfileIntegrity | None = None

    # ─────────────────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def hash_string(text: str) -> str:
        return PasswordHasher.hash_string(text, DBManager.PBKDF2_ITERATIONS)

    @staticmethod
    def _hash_v1(text: str) -> str:
        return PasswordHasher.hash_v1(text)

    @staticmethod
    def _hash_fixed_salt(text: str) -> str:
        return PasswordHasher.hash_fixed_salt(text, DBManager.LEGACY_HASH_SALT)

    @staticmethod
    def _verify_pbkdf2(text: str, stored_hash: str) -> bool:
        return PasswordHasher.verify_pbkdf2(text, stored_hash)

    @staticmethod
    def verify_secret(text: str, stored_hash: str) -> bool:
        return PasswordHasher.verify_secret(text, stored_hash, DBManager.LEGACY_HASH_SALT)

    @staticmethod
    def is_legacy_hash(text: str, stored_hash: str) -> bool:
        return PasswordHasher.is_legacy_hash(text, stored_hash, DBManager.LEGACY_HASH_SALT)

    @staticmethod
    def data_dir() -> str:
        """Restituisce la cartella dei dati radice all'interno di asset."""
        return AppPaths.data_dir()

    @staticmethod
    def normalize_username(username: str) -> str:
        """Restituisce lo username canonico usato per lookup e filename."""
        return CredentialValidator.normalize_username(username)

    @staticmethod
    def username_validation_error(username: str) -> str | None:
        return CredentialValidator.username_validation_error(username)

    @staticmethod
    def is_valid_username(username: str) -> bool:
        return CredentialValidator.is_valid_username(username)

    @staticmethod
    def _canonical_username_or_raise(username: str) -> str:
        return CredentialValidator.canonical_username_or_raise(username)

    @staticmethod
    def password_validation_error(password: str) -> str | None:
        return CredentialValidator.password_validation_error(password)

    @staticmethod
    def user_data_dir() -> str:
        """Restituisce la cartella scrivibile dei dati utente, fuori da asset."""
        return AppPaths.user_data_dir()

    @staticmethod
    def profiles_dir() -> str:
        """Restituisce la cartella profili scrivibile."""
        return DBManager._get_profile_store().profiles_dir()

    @staticmethod
    def legacy_profiles_dir() -> str:
        """Restituisce la vecchia cartella profili dentro asset/data."""
        return DBManager._get_profile_store().legacy_profiles_dir()

    @staticmethod
    def _migrate_legacy_profiles() -> None:
        """Copia i vecchi profili da asset/data/profiles solo se esplicitamente richiesto."""
        store = DBManager._get_profile_store()
        store.profiles_migrated = DBManager._profiles_migrated
        store.migrate_legacy_profiles(DBManager.legacy_profiles_dir())
        DBManager._profiles_migrated = store.profiles_migrated

    @staticmethod
    def profile_path(username: str) -> str:
        """Restituisce il percorso del file JSON dell'utente nella cartella scrivibile."""
        DBManager._migrate_legacy_profiles()
        path = DBManager._get_profile_store().profile_path(username)
        DBManager._profiles_migrated = DBManager._get_profile_store().profiles_migrated
        return path

    @staticmethod
    def _get_lockout_store() -> LockoutStore:
        if DBManager._lockout_store is None:
            DBManager._lockout_store = LockoutStore(
                lambda: DBManager.user_data_dir(),
                lambda username: DBManager.normalize_username(username),
                max_failed_attempts=DBManager.MAX_FAILED_ATTEMPTS,
                lockout_seconds=DBManager.LOCKOUT_SECONDS,
            )
        DBManager._lockout_store.max_failed_attempts = DBManager.MAX_FAILED_ATTEMPTS
        DBManager._lockout_store.lockout_seconds = DBManager.LOCKOUT_SECONDS
        return DBManager._lockout_store

    @staticmethod
    def _get_content_store() -> ContentStore:
        if DBManager._content_store is None:
            DBManager._content_store = ContentStore(lambda: DBManager.data_dir(), cache=DBManager._json_cache)
        return DBManager._content_store

    @staticmethod
    def _get_profile_store() -> ProfileStore:
        if DBManager._profile_store is None:
            DBManager._profile_store = ProfileStore(
                lambda: DBManager.user_data_dir(),
                lambda: DBManager.data_dir(),
                lambda username: DBManager._canonical_username_or_raise(username),
                profile_integrity=DBManager._get_profile_integrity(),
            )
        return DBManager._profile_store

    @staticmethod
    def _get_profile_integrity() -> ProfileIntegrity:
        if DBManager._profile_integrity is None:
            # Compatibilita con profili creati prima della firma HMAC.
            # Dopo il primo update, ProfileStore riscrive il profilo firmato.
            DBManager._profile_integrity = ProfileIntegrity(allow_unsigned_profiles=True)
        return DBManager._profile_integrity

    @staticmethod
    def _get_progress_service() -> ProgressService:
        if DBManager._progress_service is None:
            DBManager._progress_service = ProgressService(
                lambda username: DBManager.get_user_data(username),
                lambda username, data: DBManager.update_user_data(username, data),
            )
        return DBManager._progress_service

    @staticmethod
    def _get_auth_service() -> AuthService:
        if DBManager._auth_service is None:
            DBManager._auth_service = AuthService(
                lambda username: DBManager.normalize_username(username),
                lambda username: DBManager._canonical_username_or_raise(username),
                lambda password: DBManager.password_validation_error(password),
                lambda text: DBManager.hash_string(text),
                lambda text, stored_hash: DBManager.verify_secret(text, stored_hash),
                lambda text, stored_hash: DBManager.is_legacy_hash(text, stored_hash),
                lambda username: DBManager.get_user_data(username),
                lambda username, data: DBManager.update_user_data(username, data),
                lambda username, data: DBManager._get_profile_store().create_user_data(username, data),
                lambda: DBManager._migrate_legacy_profiles(),
            )
        return DBManager._auth_service

    # ─────────────────────────────────────────────────────────────────────────
    # Lockout persistente (login / recupero)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _lockouts_path() -> str:
        return DBManager._get_lockout_store().path()

    @staticmethod
    def _read_lockouts() -> dict:
        return DBManager._get_lockout_store().read()

    @staticmethod
    def _write_lockouts(data: dict) -> None:
        DBManager._get_lockout_store().write(data)

    @staticmethod
    def is_locked_out(username: str, context: str = "login") -> tuple[bool, int]:
        """Restituisce (è_bloccato, secondi_rimanenti). Pulisce le voci scadute."""
        return DBManager._get_lockout_store().is_locked_out(username, context)

    @staticmethod
    def record_failed_attempt(username: str, context: str = "login") -> bool:
        """Registra un tentativo fallito. Restituisce True se ora bloccato."""
        return DBManager._get_lockout_store().record_failed_attempt(username, context)

    @staticmethod
    def remaining_attempts(username: str, context: str = "login") -> int:
        """Restituisce i tentativi rimasti prima del blocco."""
        return DBManager._get_lockout_store().remaining_attempts(username, context)

    @staticmethod
    def clear_failed_attempts(username: str, context: str = "login") -> None:
        """Azzera il contatore tentativi dopo un login/recupero riuscito."""
        DBManager._get_lockout_store().clear_failed_attempts(username, context)

    # ─────────────────────────────────────────────────────────────────────────
    # CRUD utente
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def user_exists(username: str) -> bool:
        DBManager._migrate_legacy_profiles()
        return DBManager._get_profile_store().user_exists(username)

    @staticmethod
    def get_user_data(username: str) -> dict | None:
        DBManager._migrate_legacy_profiles()
        return DBManager._get_profile_store().get_user_data(username)

    @staticmethod
    def update_user_data(username: str, data: dict) -> None:
        DBManager._migrate_legacy_profiles()
        DBManager._get_profile_store().update_user_data(username, data)

    @staticmethod
    def verify_login(username: str, password: str) -> bool:
        return DBManager._get_auth_service().verify_login(username, password)

    @staticmethod
    def create_account(username: str, password: str, question: str, answer: str) -> None:
        DBManager._get_auth_service().create_account(username, password, question, answer)

    @staticmethod
    def delete_account(username: str) -> None:
        DBManager._migrate_legacy_profiles()
        DBManager._get_profile_store().delete_account(username)

    @staticmethod
    def export_safe_profile(username: str) -> dict | None:
        """Restituisce il profilo senza campi sensibili, pronto per l'esportazione."""
        return DBManager._get_auth_service().export_safe_profile(username)

    # ─────────────────────────────────────────────────────────────────────────
    # Achievement
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def unlock_achievement(username: str, achievement_id: str) -> bool:
        """
        Sblocca un achievement se non già posseduto.
        Restituisce True se appena sbloccato (nuovo), False se già posseduto.
        """
        return DBManager._get_progress_service().unlock_achievement(username, achievement_id)

    @staticmethod
    def check_and_unlock(username: str, achievement_id: str, notify_fn=None) -> None:
        """Sblocca e opzionalmente notifica l'utente via callback."""
        DBManager._get_progress_service().check_and_unlock(username, achievement_id, notify_fn)

    # ─────────────────────────────────────────────────────────────────────────
    # Dati statici JSON
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_static_json(filename: str, data: object) -> bool:
        return DBManager._get_content_store().validate_static_json(filename, data)

    @staticmethod
    def load_json(filename: str):
        """Carica un file JSON dalla cartella asset/data. Restituisce None se non trovato."""
        return DBManager._get_content_store().load_json(filename)

    @staticmethod
    def clear_json_cache(filename: str | None = None) -> None:
        """Svuota la cache dei JSON statici, utile durante sviluppo e test."""
        DBManager._get_content_store().clear_cache(filename)

    # ─────────────────────────────────────────────────────────────────────────
    # Statistiche
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def increment_stat(
        username: str,
        stat_key: str,
        amount: int = 1,
        unique_id: str | None = None,
        total_items: int | None = None,
    ) -> list[str]:
        """Incrementa una statistica numerica nel profilo utente."""
        return DBManager._get_progress_service().increment_stat(
            username,
            stat_key,
            amount=amount,
            unique_id=unique_id,
            total_items=total_items,
        )

    @staticmethod
    def record_quiz_result(
        username: str,
        mode_key: str,
        score: int,
        total_questions: int = 10,
        max_streak: int | None = None,
    ) -> list[str]:
        """
        Salva il risultato di un quiz e sblocca eventuali achievement.
        Restituisce la lista degli achievement appena sbloccati.
        """
        return DBManager._get_progress_service().record_quiz_result(
            username,
            mode_key,
            score,
            total_questions=total_questions,
            max_streak=max_streak,
        )
