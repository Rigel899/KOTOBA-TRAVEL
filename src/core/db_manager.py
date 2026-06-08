"""
core/db_manager.py
Gestione persistenza utenti, punteggi e achievement.
I dati statici sono salvati in asset/data.
I profili utente scrivibili sono salvati fuori da asset, nella cartella utente.
"""

import json
import logging
import os
import shutil
import hashlib
import hmac
import secrets
import stat
import tempfile
import threading
import time
from datetime import datetime

_log = logging.getLogger("kotoba.db")


class DBManager:
    current_username: str = "Viandante"
    LEGACY_HASH_SALT = "kotoba_travel_local_v2"
    PBKDF2_ITERATIONS = 210_000
    PASSWORD_MIN_LENGTH = 8
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 24
    USERNAME_ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    _json_cache: dict[str, tuple[int, object]] = {}
    _profile_lock = threading.RLock()
    _profiles_migrated = False
    MAX_FAILED_ATTEMPTS: int = 5
    LOCKOUT_SECONDS: int = 30
    _lockout_lock = threading.Lock()

    # ─────────────────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def hash_string(text: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            text.encode(),
            salt.encode(),
            DBManager.PBKDF2_ITERATIONS,
        ).hex()
        return f"pbkdf2_sha256${DBManager.PBKDF2_ITERATIONS}${salt}${digest}"

    @staticmethod
    def _hash_v1(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    @staticmethod
    def _hash_fixed_salt(text: str) -> str:
        payload = f"{DBManager.LEGACY_HASH_SALT}:{text}".encode()
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _verify_pbkdf2(text: str, stored_hash: str) -> bool:
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
    def verify_secret(text: str, stored_hash: str) -> bool:
        if not stored_hash:
            return False
        if stored_hash.startswith("pbkdf2_sha256$"):
            return DBManager._verify_pbkdf2(text, stored_hash)
        return (
            hmac.compare_digest(stored_hash, DBManager._hash_fixed_salt(text))
            or hmac.compare_digest(stored_hash, DBManager._hash_v1(text))
        )

    @staticmethod
    def is_legacy_hash(text: str, stored_hash: str) -> bool:
        return bool(stored_hash) and not stored_hash.startswith("pbkdf2_sha256$") and DBManager.verify_secret(text, stored_hash)

    @staticmethod
    def data_dir() -> str:
        """Restituisce la cartella dei dati radice all'interno di asset."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        d = os.path.join(base, "asset", "data")
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def normalize_username(username: str) -> str:
        """Restituisce lo username canonico usato per lookup e filename."""
        return (username or "").strip().lower()

    @staticmethod
    def username_validation_error(username: str) -> str | None:
        normalized = DBManager.normalize_username(username)
        if not normalized:
            return "Inserisci un nome utente."
        if len(normalized) < DBManager.USERNAME_MIN_LENGTH:
            return f"Il nome utente deve avere almeno {DBManager.USERNAME_MIN_LENGTH} caratteri."
        if len(normalized) > DBManager.USERNAME_MAX_LENGTH:
            return f"Il nome utente deve avere al massimo {DBManager.USERNAME_MAX_LENGTH} caratteri."
        if any(ch not in DBManager.USERNAME_ALLOWED_CHARS for ch in normalized):
            return "Usa solo lettere, numeri o underscore nel nome utente."
        return None

    @staticmethod
    def is_valid_username(username: str) -> bool:
        return DBManager.username_validation_error(username) is None

    @staticmethod
    def _canonical_username_or_raise(username: str) -> str:
        error = DBManager.username_validation_error(username)
        if error:
            raise ValueError(error)
        return DBManager.normalize_username(username)

    @staticmethod
    def password_validation_error(password: str) -> str | None:
        if not password:
            return "Inserisci una password."
        if len(password) < DBManager.PASSWORD_MIN_LENGTH:
            return f"La password deve essere di almeno {DBManager.PASSWORD_MIN_LENGTH} caratteri."
        return None

    @staticmethod
    def user_data_dir() -> str:
        """Restituisce la cartella scrivibile dei dati utente, fuori da asset."""
        appdata = os.environ.get("APPDATA")
        if appdata:
            d = os.path.join(appdata, "KotobaTravel")
        else:
            d = os.path.join(os.path.expanduser("~"), ".kotoba_travel")
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def profiles_dir() -> str:
        """Restituisce la cartella profili scrivibile."""
        d = os.path.join(DBManager.user_data_dir(), "profiles")
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def legacy_profiles_dir() -> str:
        """Restituisce la vecchia cartella profili dentro asset/data."""
        return os.path.join(DBManager.data_dir(), "profiles")

    @staticmethod
    def _migrate_legacy_profiles() -> None:
        """Copia i vecchi profili da asset/data/profiles solo se esplicitamente richiesto."""
        if DBManager._profiles_migrated:
            return
        DBManager._profiles_migrated = True

        if os.environ.get("KOTOBA_MIGRATE_LEGACY_PROFILES") != "1":
            return

        old_dir = DBManager.legacy_profiles_dir()
        if not os.path.isdir(old_dir):
            return

        new_dir = DBManager.profiles_dir()
        for filename in os.listdir(old_dir):
            if not (filename.startswith("user_") and filename.endswith(".json")):
                continue
            src = os.path.join(old_dir, filename)
            dst = os.path.join(new_dir, filename)
            if os.path.exists(dst):
                continue
            try:
                shutil.copy2(src, dst)
            except OSError:
                pass

    @staticmethod
    def profile_path(username: str) -> str:
        """Restituisce il percorso del file JSON dell'utente nella cartella scrivibile."""
        DBManager._migrate_legacy_profiles()
        safe = DBManager._canonical_username_or_raise(username)
        return os.path.join(DBManager.profiles_dir(), f"user_{safe}.json")

    # ─────────────────────────────────────────────────────────────────────────
    # Lockout persistente (login / recupero)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _lockouts_path() -> str:
        return os.path.join(DBManager.user_data_dir(), "lockouts.json")

    @staticmethod
    def _read_lockouts() -> dict:
        path = DBManager._lockouts_path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _write_lockouts(data: dict) -> None:
        path = DBManager._lockouts_path()
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
                except OSError:
                    pass

    @staticmethod
    def is_locked_out(username: str, context: str = "login") -> tuple[bool, int]:
        """Restituisce (è_bloccato, secondi_rimanenti). Pulisce le voci scadute."""
        username = DBManager.normalize_username(username)
        if not username:
            return False, 0
        key = f"{username}:{context}"
        with DBManager._lockout_lock:
            lockouts = DBManager._read_lockouts()
            entry = lockouts.get(key, {})
            locked_until = entry.get("locked_until")
            if locked_until:
                remaining = locked_until - time.time()
                if remaining > 0:
                    return True, int(remaining) + 1
                entry.pop("locked_until", None)
                entry["attempts"] = 0
                lockouts[key] = entry
                DBManager._write_lockouts(lockouts)
        return False, 0

    @staticmethod
    def record_failed_attempt(username: str, context: str = "login") -> bool:
        """Registra un tentativo fallito. Restituisce True se ora bloccato."""
        username = DBManager.normalize_username(username)
        if not username:
            return False
        key = f"{username}:{context}"
        with DBManager._lockout_lock:
            lockouts = DBManager._read_lockouts()
            entry = lockouts.setdefault(key, {"attempts": 0})
            entry["attempts"] = entry.get("attempts", 0) + 1
            if entry["attempts"] >= DBManager.MAX_FAILED_ATTEMPTS:
                entry["locked_until"] = time.time() + DBManager.LOCKOUT_SECONDS
                entry["attempts"] = 0
                lockouts[key] = entry
                DBManager._write_lockouts(lockouts)
                return True
            lockouts[key] = entry
            DBManager._write_lockouts(lockouts)
            return False

    @staticmethod
    def remaining_attempts(username: str, context: str = "login") -> int:
        """Restituisce i tentativi rimasti prima del blocco."""
        username = DBManager.normalize_username(username)
        if not username:
            return DBManager.MAX_FAILED_ATTEMPTS
        key = f"{username}:{context}"
        with DBManager._lockout_lock:
            lockouts = DBManager._read_lockouts()
            entry = lockouts.get(key, {})
            return max(0, DBManager.MAX_FAILED_ATTEMPTS - entry.get("attempts", 0))

    @staticmethod
    def clear_failed_attempts(username: str, context: str = "login") -> None:
        """Azzera il contatore tentativi dopo un login/recupero riuscito."""
        username = DBManager.normalize_username(username)
        if not username:
            return
        key = f"{username}:{context}"
        with DBManager._lockout_lock:
            lockouts = DBManager._read_lockouts()
            if key in lockouts:
                del lockouts[key]
                DBManager._write_lockouts(lockouts)

    # ─────────────────────────────────────────────────────────────────────────
    # CRUD utente
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def user_exists(username: str) -> bool:
        try:
            return os.path.exists(DBManager.profile_path(username))
        except ValueError:
            return False

    @staticmethod
    def get_user_data(username: str) -> dict | None:
        try:
            path = DBManager.profile_path(username)
        except ValueError:
            return None
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            _log.warning("profile read failed for %s: %s", username, exc)
            return None

    @staticmethod
    def update_user_data(username: str, data: dict) -> None:
        path = DBManager.profile_path(username)
        profiles_dir = os.path.dirname(path)
        tmp_path = None
        fd = None

        def write_payload(f) -> None:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())

        with DBManager._profile_lock:
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

                # Windows puo tenere il file profilo bloccato per qualche
                # istante; riproviamo prima di rinunciare all'atomic replace.
                for attempt in range(6):
                    try:
                        if os.path.exists(path):
                            try:
                                os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
                            except OSError:
                                pass
                        os.replace(tmp_path, path)
                        return
                    except PermissionError:
                        if attempt == 5:
                            break
                        time.sleep(0.05 * (attempt + 1))

                # Fallback raro: meglio salvare in modo non atomico che
                # far cadere l'intera app durante un click dell'utente.
                with open(path, "w", encoding="utf-8") as f:
                    write_payload(f)
            finally:
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

    @staticmethod
    def verify_login(username: str, password: str) -> bool:
        username = DBManager.normalize_username(username)
        data = DBManager.get_user_data(username)
        if not data:
            return False
        stored_hash = data.get("password_hash", "")
        if not DBManager.verify_secret(password, stored_hash):
            return False
        if DBManager.is_legacy_hash(password, stored_hash):
            data["password_hash"] = DBManager.hash_string(password)
            DBManager.update_user_data(username, data)
        return True

    @staticmethod
    def create_account(username: str, password: str, question: str, answer: str) -> None:
        username = DBManager._canonical_username_or_raise(username)
        password_error = DBManager.password_validation_error(password)
        if password_error:
            raise ValueError(password_error)
        data = {
            "username": username,
            "password_hash": DBManager.hash_string(password),
            "recovery_question": question,
            "recovery_answer_hash": DBManager.hash_string(answer),
            "achievements": [],
            "scores": {
                "hiragana": 0,
                "katakana": 0,
                "mixed": 0,
                "kanji": 0,
                "vocab": 0,
                "grammar": 0,
                "exam": 0,
            },
            "stats": {
                "total_quizzes": 0,
                "total_questions": 0,
                "total_correct": 0,
                "max_streak": 0,
                "perfect_quizzes": 0,
                "quiz_modes": {},
                "quiz_mode_correct": {},
                "quiz_mode_total": {},
                "perfect_quiz_modes": {},
                "food_viewed": 0,
                "places_viewed": 0,
                "culture_viewed": 0,
                "history_viewed": 0,
            },
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
        }
        path = DBManager.profile_path(username)
        with DBManager._profile_lock:
            if os.path.exists(path):
                raise ValueError(f"Il nome utente '{username}' è già in uso.")
            DBManager.update_user_data(username, data)

    @staticmethod
    def delete_account(username: str) -> None:
        try:
            p = DBManager.profile_path(username)
        except ValueError:
            return
        with DBManager._profile_lock:
            if os.path.exists(p):
                os.remove(p)

    @staticmethod
    def export_safe_profile(username: str) -> dict | None:
        """Restituisce il profilo senza campi sensibili, pronto per l'esportazione."""
        data = DBManager.get_user_data(username)
        if not data:
            return None
        _SENSITIVE = {"password_hash", "recovery_answer_hash"}
        safe = {k: v for k, v in data.items() if k not in _SENSITIVE}
        safe["_export_note"] = "Hash di sicurezza non inclusi. Solo dati di progresso."
        safe["_exported_at"] = datetime.now().isoformat()
        return safe

    # ─────────────────────────────────────────────────────────────────────────
    # Accesso rapido all'utente corrente
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def current_user_data() -> dict:
        return DBManager.get_user_data(DBManager.current_username) or {}

    @staticmethod
    def save_current_user(data: dict) -> None:
        if DBManager.current_username != "Viandante":
            DBManager.update_user_data(DBManager.current_username, data)

    # ─────────────────────────────────────────────────────────────────────────
    # Achievement
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def unlock_achievement(username: str, achievement_id: str) -> bool:
        """
        Sblocca un achievement se non già posseduto.
        Restituisce True se appena sbloccato (nuovo), False se già posseduto.
        """
        data = DBManager.get_user_data(username)
        if not data:
            return False
        if achievement_id not in data.get("achievements", []):
            data.setdefault("achievements", []).append(achievement_id)
            DBManager.update_user_data(username, data)
            return True
        return False

    @staticmethod
    def check_and_unlock(username: str, achievement_id: str, notify_fn=None) -> None:
        """Sblocca e opzionalmente notifica l'utente via callback."""
        if DBManager.unlock_achievement(username, achievement_id):
            if notify_fn:
                from src.core.achievements import ACHIEVEMENTS
                ach = ACHIEVEMENTS.get(achievement_id)
                if ach:
                    notify_fn(ach)

    # ─────────────────────────────────────────────────────────────────────────
    # Dati statici JSON
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def load_json(filename: str):
        """Carica un file JSON dalla cartella asset/data. Restituisce None se non trovato."""
        path = os.path.join(DBManager.data_dir(), filename)
        if not os.path.exists(path):
            return None
        try:
            mtime_ns = os.stat(path).st_mtime_ns
            cached = DBManager._json_cache.get(path)
            if cached and cached[0] == mtime_ns:
                return cached[1]
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            DBManager._json_cache[path] = (mtime_ns, data)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            _log.warning("json load failed for %s: %s", path, exc)
            DBManager._json_cache.pop(path, None)
            return None

    @staticmethod
    def clear_json_cache(filename: str | None = None) -> None:
        """Svuota la cache dei JSON statici, utile durante sviluppo e test."""
        if filename is None:
            DBManager._json_cache.clear()
            return
        path = os.path.join(DBManager.data_dir(), filename)
        DBManager._json_cache.pop(path, None)

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
        data = DBManager.get_user_data(username)
        if not data:
            return []

        stats = data.setdefault("stats", {})

        unique_count: int | None = None
        if unique_id:
            unique_views = stats.setdefault("unique_views", {})
            viewed_ids = unique_views.setdefault(stat_key, {})
            if isinstance(viewed_ids, list):
                viewed_ids = {item: 1 for item in viewed_ids}
                unique_views[stat_key] = viewed_ids
            if unique_id in viewed_ids:
                return []
            viewed_ids[unique_id] = 1
            unique_count = len(viewed_ids)
            stats[stat_key] = max(stats.get(stat_key, 0), unique_count)
        else:
            stats[stat_key] = stats.get(stat_key, 0) + amount

        DBManager.update_user_data(username, data)

        checks: list[str] = []
        value = unique_count if unique_count is not None else stats[stat_key]
        if stat_key == "food_viewed" and value >= 10:
            checks.append("food_10")
        elif stat_key == "places_viewed" and value >= 5:
            checks.append("places_5")
        elif stat_key == "culture_viewed":
            if total_items and value >= total_items:
                checks.append("culture_all")
        elif stat_key == "history_viewed":
            if total_items and value >= total_items:
                checks.append("history_all")

        newly_unlocked = []
        for ach_id in checks:
            if DBManager.unlock_achievement(username, ach_id):
                newly_unlocked.append(ach_id)
        return newly_unlocked

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
        data = DBManager.get_user_data(username)
        if not data:
            return []

        # Aggiorna punteggio massimo per la modalità
        total_questions = max(1, int(total_questions or 1))
        correct_count = max(0, min(int(score or 0), total_questions))
        score_out_of_ten = round((correct_count / total_questions) * 10)
        streak_count = max(0, min(int(max_streak if max_streak is not None else correct_count), total_questions))
        is_perfect = correct_count == total_questions

        score_key = mode_key
        legacy_score_key = f"score_{mode_key}"
        scores = data.setdefault("scores", {})
        best_score = max(scores.get(score_key, 0), scores.pop(legacy_score_key, 0))
        scores[score_key] = max(score_out_of_ten, best_score)

        # Aggiorna statistiche generali
        stats = data.setdefault("stats", {})
        stats["total_quizzes"] = stats.get("total_quizzes", 0) + 1
        stats["total_questions"] = stats.get("total_questions", 0) + total_questions
        stats["total_correct"] = stats.get("total_correct", 0) + correct_count
        stats["max_streak"] = max(stats.get("max_streak", 0), streak_count)
        mode_counts = stats.setdefault("quiz_modes", {})
        mode_counts[mode_key] = mode_counts.get(mode_key, 0) + 1
        mode_correct = stats.setdefault("quiz_mode_correct", {})
        mode_correct[mode_key] = mode_correct.get(mode_key, 0) + correct_count
        mode_total = stats.setdefault("quiz_mode_total", {})
        mode_total[mode_key] = mode_total.get(mode_key, 0) + total_questions
        if is_perfect:
            perfect_modes = stats.setdefault("perfect_quiz_modes", {})
            perfect_modes[mode_key] = perfect_modes.get(mode_key, 0) + 1
            stats["perfect_quizzes"] = stats.get("perfect_quizzes", 0) + 1

        DBManager.update_user_data(username, data)

        # Verifica achievement e restituisce i nuovi sbloccati
        newly_unlocked = []
        total_quizzes = stats["total_quizzes"]

        checks = []
        if is_perfect and total_questions >= 10:
            if mode_key == "hiragana":
                checks.append("hiragana_perfect")
            elif mode_key == "katakana":
                checks.append("katakana_perfect")
            elif mode_key == "mixed":
                checks.append("mixed_perfect")
        if streak_count >= 10:
            checks.append("streak_10")
        if streak_count >= 5:
            checks.append("streak_5")
        if total_quizzes >= 5:
            checks.append("quiz_5")
        if total_quizzes >= 25:
            checks.append("quiz_25")
        if mode_key == "kanji":
            checks.append("kanji_first")
        if mode_key == "vocab" and mode_correct.get("vocab", 0) >= 50:
            checks.append("vocab_50")

        for ach_id in checks:
            if DBManager.unlock_achievement(username, ach_id):
                newly_unlocked.append(ach_id)

        return newly_unlocked
