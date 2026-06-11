"""
core/achievements.py
Definizioni di tutti gli achievement sbloccabili in Kotoba Travel.
"""

from src.core.settings import KotobaTheme


PLATINUM_ACHIEVEMENT = "kotoba_platinum"

RARITY_ORDER: tuple[str, ...] = (
    "comune",
    "raro",
    "molto raro",
    "epico",
    "leggendario",
)

MODULE_ORDER: tuple[str, ...] = (
    "account",
    "progress",
    "dojo_kana",
    "dojo_kanji",
    "dojo_vocab",
    "dojo_grammar",
    "prova_kotoba",
    "exploration",
    "platinum",
)

MODULE_LABELS: dict[str, str] = {
    "account": "Account",
    "progress": "Progressi",
    "dojo_kana": "Kana",
    "dojo_kanji": "Kanji",
    "dojo_vocab": "Vocabolario",
    "dojo_grammar": "Grammatica",
    "prova_kotoba": "Prova Kotoba",
    "exploration": "Esplorazione",
    "platinum": "Platino",
}

ACHIEVEMENTS: dict[str, dict] = {
    "first_steps": {
        "title": "Primo Passo",
        "description": "Hai creato il tuo account Kotoba Travel.",
        "emoji": "⛩️",
        "rarity": "comune",
        "module": "account",
    },
    "streak_5": {
        "title": "Samurai Infallibile",
        "description": "5 risposte corrette consecutive in un quiz.",
        "emoji": "⚡",
        "rarity": "comune",
        "module": "progress",
    },
    "streak_10": {
        "title": "Mente di Cristallo",
        "description": "10 risposte corrette consecutive in un quiz.",
        "emoji": "💎",
        "rarity": "raro",
        "module": "progress",
    },
    "quiz_5": {
        "title": "Allenato",
        "description": "Completati 5 quiz.",
        "emoji": "🎯",
        "rarity": "comune",
        "module": "progress",
    },
    "quiz_25": {
        "title": "Guerriero della Conoscenza",
        "description": "Completati 25 quiz.",
        "emoji": "⚔️",
        "rarity": "raro",
        "module": "progress",
    },
    "hiragana_perfect": {
        "title": "Maestro Hiragana",
        "description": "Punteggio perfetto nel quiz Hiragana.",
        "emoji": "あ",
        "rarity": "raro",
        "module": "dojo_kana",
    },
    "katakana_perfect": {
        "title": "Maestro Katakana",
        "description": "Punteggio perfetto nel quiz Katakana.",
        "emoji": "ア",
        "rarity": "raro",
        "module": "dojo_kana",
    },
    "mixed_perfect": {
        "title": "Sensei dei Sillabari",
        "description": "Punteggio perfetto nel quiz Misto Hiragana+Katakana.",
        "emoji": "仮",
        "rarity": "molto raro",
        "module": "dojo_kana",
    },
    "kanji_first": {
        "title": "L'Inizio del Kanji",
        "description": "Completato il primo quiz Kanji.",
        "emoji": "漢",
        "rarity": "comune",
        "module": "dojo_kanji",
    },
    "kanji_perfect": {
        "title": "Custode dei Kanji",
        "description": "Punteggio perfetto nel quiz Kanji.",
        "emoji": "漢",
        "rarity": "molto raro",
        "module": "dojo_kanji",
    },
    "vocab_first": {
        "title": "Prime Parole",
        "description": "Completato il primo quiz Vocabolario.",
        "emoji": "語",
        "rarity": "comune",
        "module": "dojo_vocab",
    },
    "vocab_50": {
        "title": "Dizionario Vivente",
        "description": "Raggiunte 50 risposte corrette nel quiz Vocabolario.",
        "emoji": "語",
        "rarity": "molto raro",
        "module": "dojo_vocab",
    },
    "vocab_perfect": {
        "title": "Lessico Impeccabile",
        "description": "Punteggio perfetto nel quiz Vocabolario.",
        "emoji": "語",
        "rarity": "raro",
        "module": "dojo_vocab",
    },
    "grammar_first": {
        "title": "Prima Regola",
        "description": "Completato il primo quiz Grammatica.",
        "emoji": "文",
        "rarity": "comune",
        "module": "dojo_grammar",
    },
    "grammar_perfect": {
        "title": "Architetto della Frase",
        "description": "Punteggio perfetto nel quiz Grammatica.",
        "emoji": "文",
        "rarity": "raro",
        "module": "dojo_grammar",
    },
    "exam_first": {
        "title": "Prima Prova Kotoba",
        "description": "Completata la prima Prova Kotoba.",
        "emoji": "試",
        "rarity": "comune",
        "module": "prova_kotoba",
    },
    "exam_perfect_1": {
        "title": "Prova Kotoba Perfetta",
        "description": "Punteggio perfetto nella Prova Kotoba.",
        "emoji": "試",
        "rarity": "raro",
        "module": "prova_kotoba",
    },
    "exam_perfect_5": {
        "title": "Custode Kotoba",
        "description": "5 Prove Kotoba perfette.",
        "emoji": "極",
        "rarity": "molto raro",
        "module": "prova_kotoba",
    },
    "exam_perfect_10": {
        "title": "Maestria Kotoba",
        "description": "10 Prove Kotoba perfette.",
        "emoji": "極",
        "rarity": "epico",
        "module": "prova_kotoba",
    },
    "exam_master": {
        "title": "Cintura Nera Kotoba",
        "description": "20 Prove Kotoba perfette.",
        "emoji": "黒",
        "rarity": "leggendario",
        "module": "prova_kotoba",
    },
    "food_10": {
        "title": "Gourmet del Sol Levante",
        "description": "Esplorati 10 piatti nella sezione Cibo.",
        "emoji": "弁",
        "rarity": "comune",
        "module": "exploration",
    },
    "places_5": {
        "title": "Viaggiatore Curioso",
        "description": "Visitati 5 luoghi iconici.",
        "emoji": "旅",
        "rarity": "comune",
        "module": "exploration",
    },
    "culture_all": {
        "title": "Anima Nipponica",
        "description": "Esplorati tutti i moduli della sezione Cultura.",
        "emoji": "桜",
        "rarity": "raro",
        "module": "exploration",
    },
    "history_all": {
        "title": "Studioso della Storia",
        "description": "Letti tutti gli episodi della sezione Storia.",
        "emoji": "城",
        "rarity": "raro",
        "module": "exploration",
    },
    "exploration_all": {
        "title": "Viaggio Completo",
        "description": "Hai esplorato tutto: Cibo, Luoghi, Cultura e Storia.",
        "emoji": "旅",
        "rarity": "leggendario",
        "module": "exploration",
    },
    PLATINUM_ACHIEVEMENT: {
        "title": "Kotoba Platinato",
        "description": "Hai conquistato tutti gli achievement di Kotoba Travel.",
        "emoji": "白金",
        "rarity": "leggendario",
        "module": "platinum",
        "secret": True,
        "platinum": True,
    },
}

RARITY_COLOR: dict[str, str] = {
    "comune": KotobaTheme.RARITY_COMUNE,
    "raro": KotobaTheme.RARITY_RARO,
    "molto raro": KotobaTheme.RARITY_MOLTO_RARO,
    "epico": KotobaTheme.RARITY_EPICO,
    "leggendario": KotobaTheme.RARITY_LEGGENDARIO,
}


def platinum_required_achievement_ids() -> set[str]:
    """Achievement richiesti per sbloccare il platino, escluso il platino stesso."""
    return {achievement_id for achievement_id in ACHIEVEMENTS if achievement_id != PLATINUM_ACHIEVEMENT}


def visible_achievement_items(unlocked_ids: set[str] | None = None) -> list[tuple[str, dict]]:
    """Restituisce il catalogo visibile, nascondendo gli achievement segreti bloccati."""
    unlocked = unlocked_ids or set()
    return [
        (achievement_id, data)
        for achievement_id, data in ACHIEVEMENTS.items()
        if not data.get("secret") or achievement_id in unlocked
    ]


def visible_achievement_ids(unlocked_ids: set[str] | None = None) -> list[str]:
    return [achievement_id for achievement_id, _ in visible_achievement_items(unlocked_ids)]
