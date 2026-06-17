"""
core/profile_factory.py
Costruzione del profilo utente iniziale.
"""
from __future__ import annotations

from datetime import datetime


def build_default_profile(
    username: str,
    password_hash: str,
    recovery_question: str,
    recovery_answer_hash: str,
    *,
    timestamp: str | None = None,
) -> dict:
    now = timestamp or datetime.now().isoformat()
    return {
        "username": username,
        "password_hash": password_hash,
        "recovery_question": recovery_question,
        "recovery_answer_hash": recovery_answer_hash,
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
        "created_at": now,
        "last_login": now,
    }
