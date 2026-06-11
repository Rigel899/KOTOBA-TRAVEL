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
EXPLORATION_COMPLETE_STATS: tuple[str, ...] = (
    "food_viewed",
    "places_viewed",
    "culture_viewed",
    "history_viewed",
)
EXPLORATION_ALL_ACHIEVEMENT = "exploration_all"

STUDY_SECTION_STAT = "study_sections_consulted"
STUDY_REQUIRED_SECTIONS: tuple[str, ...] = (
    "hiragana",
    "katakana",
    "kanji",
    "vocab",
    "grammar",
)
STUDY_ACHIEVEMENTS: dict[str, str] = {
    "first": "study_first",
}
STUDY_MASTERY_ACHIEVEMENT = "study_all"
STUDY_MASTERY_REQUIRED_ACHIEVEMENTS: tuple[str, ...] = (
    "mixed_perfect",
    "kanji_perfect",
    "vocab_perfect",
    "grammar_perfect",
)

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

EXAM_REQUIRED_QUESTIONS = 20
EXAM_PERFECT_MILESTONES: tuple[tuple[int, str], ...] = (
    (1, "exam_perfect_1"),
    (5, "exam_perfect_5"),
    (10, "exam_perfect_10"),
    (20, "exam_master"),
)


class ProgressService:
    def __init__(
        self,
        get_user_data: Callable[[str], dict | None],
        update_user_data: Callable[[str, dict], None],
    ) -> None:
        self._get_user_data = get_user_data
        self._update_user_data = update_user_data

    def unlock_achievement(self, username: str, achievement_id: str) -> bool:
        return achievement_id in self.unlock_achievement_ids(username, achievement_id)

    def unlock_achievement_ids(self, username: str, achievement_id: str) -> list[str]:
        from src.core.achievements import ACHIEVEMENTS, PLATINUM_ACHIEVEMENT, platinum_required_achievement_ids

        if achievement_id not in ACHIEVEMENTS:
            _log.warning("refusing to unlock unknown achievement id: %s", achievement_id)
            return []

        data = self._get_user_data(username)
        if not data:
            return []

        achievements = data.setdefault("achievements", [])
        if achievement_id == STUDY_MASTERY_ACHIEVEMENT:
            if not set(STUDY_MASTERY_REQUIRED_ACHIEVEMENTS).issubset(set(achievements)):
                return []
        if achievement_id == PLATINUM_ACHIEVEMENT:
            if not platinum_required_achievement_ids().issubset(set(achievements)):
                return []

        newly_unlocked = []
        if achievement_id not in achievements:
            achievements.append(achievement_id)
            newly_unlocked.append(achievement_id)

        if achievement_id != STUDY_MASTERY_ACHIEVEMENT and STUDY_MASTERY_ACHIEVEMENT not in achievements:
            if set(STUDY_MASTERY_REQUIRED_ACHIEVEMENTS).issubset(set(achievements)):
                achievements.append(STUDY_MASTERY_ACHIEVEMENT)
                newly_unlocked.append(STUDY_MASTERY_ACHIEVEMENT)

        if achievement_id != PLATINUM_ACHIEVEMENT and PLATINUM_ACHIEVEMENT not in achievements:
            if platinum_required_achievement_ids().issubset(set(achievements)):
                achievements.append(PLATINUM_ACHIEVEMENT)
                newly_unlocked.append(PLATINUM_ACHIEVEMENT)

        if newly_unlocked:
            self._update_user_data(username, data)
        return newly_unlocked

    def check_and_unlock(self, username: str, achievement_id: str, notify_fn=None) -> None:
        newly_unlocked = self.unlock_achievement_ids(username, achievement_id)
        if newly_unlocked and notify_fn:
            if notify_fn:
                from src.core.achievements import ACHIEVEMENTS

                for unlocked_id in newly_unlocked:
                    ach = ACHIEVEMENTS.get(unlocked_id)
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
        exploration_totals = stats.setdefault("exploration_totals", {})
        if total_items and total_items > 0:
            exploration_totals[stat_key] = int(total_items)

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
        elif stat_key == STUDY_SECTION_STAT:
            checks.append(STUDY_ACHIEVEMENTS["first"])

        if all(exploration_totals.get(key, 0) for key in EXPLORATION_COMPLETE_STATS):
            if all(stats.get(key, 0) >= exploration_totals.get(key, 0) for key in EXPLORATION_COMPLETE_STATS):
                checks.append(EXPLORATION_ALL_ACHIEVEMENT)

        newly_unlocked = []
        for ach_id in checks:
            newly_unlocked.extend(self.unlock_achievement_ids(username, ach_id))
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
        mode_best_correct = stats.setdefault("quiz_mode_best_correct", {})
        mode_best_total = stats.setdefault("quiz_mode_best_total", {})
        previous_best_correct = int(mode_best_correct.get(mode_key, 0) or 0)
        previous_best_total = int(mode_best_total.get(mode_key, 0) or 0)
        previous_ratio = (previous_best_correct / previous_best_total) if previous_best_total else -1
        current_ratio = correct_count / total_questions
        if current_ratio > previous_ratio or (
            current_ratio == previous_ratio and correct_count > previous_best_correct
        ):
            mode_best_correct[mode_key] = correct_count
            mode_best_total[mode_key] = total_questions
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
        perfect_eligible = is_perfect and total_questions >= 10
        if mode_key == "exam":
            perfect_eligible = is_perfect and total_questions >= EXAM_REQUIRED_QUESTIONS

        if perfect_eligible:
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
        if mode_key == "exam" and perfect_eligible:
            perfect_count = int(stats.get("perfect_quiz_modes", {}).get("exam", 0) or 0)
            for threshold, achievement_id in EXAM_PERFECT_MILESTONES:
                if perfect_count >= threshold:
                    checks.append(achievement_id)

        for ach_id in checks:
            newly_unlocked.extend(self.unlock_achievement_ids(username, ach_id))

        return newly_unlocked
