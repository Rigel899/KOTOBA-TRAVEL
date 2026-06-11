"""
core/progress_service.py
Statistiche, risultati quiz e achievement del profilo utente.
"""
from __future__ import annotations

from collections.abc import Callable
import logging


_log = logging.getLogger("kotoba.progress")

EXPLORATION_ACHIEVEMENTS: dict[str, str] = {
    "food_viewed": "food_10",
    "places_viewed": "places_5",
    "culture_viewed": "culture_all",
    "history_viewed": "history_all",
}

QUIZ_FIRST_ACHIEVEMENTS: dict[str, str] = {
    "kanji": "kanji_first",
    "vocab": "vocab_first",
    "grammar": "grammar_first",
    "exam": "exam_first",
}

QUIZ_PERFECT_ACHIEVEMENTS: dict[str, str] = {
    "hiragana": "hiragana_perfect",
    "katakana": "katakana_perfect",
    "mixed": "mixed_perfect",
    "kanji": "kanji_perfect",
    "vocab": "vocab_perfect",
    "grammar": "grammar_perfect",
}

EXAM_PASS_ACHIEVEMENT = "exam_passed"
EXAM_MASTER_ACHIEVEMENT = "exam_master"
EXAM_PASS_THRESHOLD = 0.70
EXAM_MASTER_THRESHOLD = 0.90
EXAM_REQUIRED_QUESTIONS = 20


class ProgressService:
    def __init__(
        self,
        get_user_data: Callable[[str], dict | None],
        update_user_data: Callable[[str, dict], None],
    ) -> None:
        self._get_user_data = get_user_data
        self._update_user_data = update_user_data

    def unlock_achievement(self, username: str, achievement_id: str) -> bool:
        from src.core.achievements import ACHIEVEMENTS

        if achievement_id not in ACHIEVEMENTS:
            _log.warning("refusing to unlock unknown achievement id: %s", achievement_id)
            return False

        data = self._get_user_data(username)
        if not data:
            return False
        if achievement_id not in data.get("achievements", []):
            data.setdefault("achievements", []).append(achievement_id)
            self._update_user_data(username, data)
            return True
        return False

    def check_and_unlock(self, username: str, achievement_id: str, notify_fn=None) -> None:
        if self.unlock_achievement(username, achievement_id):
            if notify_fn:
                from src.core.achievements import ACHIEVEMENTS

                ach = ACHIEVEMENTS.get(achievement_id)
                if ach:
                    notify_fn(ach)

    def increment_stat(
        self,
        username: str,
        stat_key: str,
        amount: int = 1,
        unique_id: str | None = None,
        total_items: int | None = None,
    ) -> list[str]:
        data = self._get_user_data(username)
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

        self._update_user_data(username, data)

        checks: list[str] = []
        value = unique_count if unique_count is not None else stats[stat_key]
        if stat_key == "food_viewed" and value >= 10:
            checks.append(EXPLORATION_ACHIEVEMENTS["food_viewed"])
        elif stat_key == "places_viewed" and value >= 5:
            checks.append(EXPLORATION_ACHIEVEMENTS["places_viewed"])
        elif stat_key == "culture_viewed":
            if total_items and value >= total_items:
                checks.append(EXPLORATION_ACHIEVEMENTS["culture_viewed"])
        elif stat_key == "history_viewed":
            if total_items and value >= total_items:
                checks.append(EXPLORATION_ACHIEVEMENTS["history_viewed"])

        newly_unlocked = []
        for ach_id in checks:
            if self.unlock_achievement(username, ach_id):
                newly_unlocked.append(ach_id)
        return newly_unlocked

    def record_quiz_result(
        self,
        username: str,
        mode_key: str,
        score: int,
        total_questions: int = 10,
        max_streak: int | None = None,
    ) -> list[str]:
        data = self._get_user_data(username)
        if not data:
            return []

        total_questions = max(1, int(total_questions or 1))
        correct_count = max(0, min(int(score or 0), total_questions))
        score_out_of_ten = round((correct_count / total_questions) * 10)
        streak_count = max(0, min(int(max_streak if max_streak is not None else correct_count), total_questions))
        is_perfect = correct_count == total_questions
        accuracy = correct_count / total_questions

        score_key = mode_key
        legacy_score_key = f"score_{mode_key}"
        scores = data.setdefault("scores", {})
        best_score = max(scores.get(score_key, 0), scores.pop(legacy_score_key, 0))
        scores[score_key] = max(score_out_of_ten, best_score)

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

        self._update_user_data(username, data)

        newly_unlocked = []
        total_quizzes = stats["total_quizzes"]

        checks = []
        first_achievement = QUIZ_FIRST_ACHIEVEMENTS.get(mode_key)
        if first_achievement:
            checks.append(first_achievement)
        if is_perfect and total_questions >= 10:
            perfect_achievement = QUIZ_PERFECT_ACHIEVEMENTS.get(mode_key)
            if perfect_achievement:
                checks.append(perfect_achievement)
        if streak_count >= 10:
            checks.append("streak_10")
        if streak_count >= 5:
            checks.append("streak_5")
        if total_quizzes >= 5:
            checks.append("quiz_5")
        if total_quizzes >= 25:
            checks.append("quiz_25")
        if mode_key == "vocab" and mode_correct.get("vocab", 0) >= 50:
            checks.append("vocab_50")
        if mode_key == "exam":
            if total_questions >= EXAM_REQUIRED_QUESTIONS and accuracy >= EXAM_PASS_THRESHOLD:
                checks.append(EXAM_PASS_ACHIEVEMENT)
            if total_questions >= EXAM_REQUIRED_QUESTIONS and accuracy >= EXAM_MASTER_THRESHOLD:
                checks.append(EXAM_MASTER_ACHIEVEMENT)

        for ach_id in checks:
            if self.unlock_achievement(username, ach_id):
                newly_unlocked.append(ach_id)

        return newly_unlocked
