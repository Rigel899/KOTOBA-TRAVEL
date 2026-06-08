"""
core/achievements.py
Definizioni di tutti gli achievement sbloccabili in Kotoba Travel.
"""

from src.core.settings import KotobaTheme

# ─────────────────────────────────────────────────────────────────────────────
# Dizionario principale degli achievement
# ─────────────────────────────────────────────────────────────────────────────
ACHIEVEMENTS: dict[str, dict] = {
    # Onboarding
    "first_steps": {
        "title": "Primo Passo",
        "description": "Hai creato il tuo account Kotoba Travel.",
        "emoji": "⛩️",
        "rarity": "comune",
    },
    # Kana quiz
    "hiragana_perfect": {
        "title": "Maestro Hiragana",
        "description": "Punteggio perfetto (10/10) nel quiz Hiragana.",
        "emoji": "あ",
        "rarity": "raro",
    },
    "katakana_perfect": {
        "title": "Maestro Katakana",
        "description": "Punteggio perfetto (10/10) nel quiz Katakana.",
        "emoji": "ア",
        "rarity": "raro",
    },
    "mixed_perfect": {
        "title": "Sensei dei Sillabari",
        "description": "Punteggio perfetto nel quiz Misto Hiragana+Katakana.",
        "emoji": "👑",
        "rarity": "epico",
    },
    # Streak
    "streak_5": {
        "title": "Samurai Infallibile",
        "description": "5 risposte corrette consecutive in un quiz.",
        "emoji": "⚡",
        "rarity": "comune",
    },
    "streak_10": {
        "title": "Mente di Cristallo",
        "description": "10 risposte corrette consecutive in un quiz.",
        "emoji": "💎",
        "rarity": "non comune",
    },
    # Quiz count
    "quiz_5": {
        "title": "Allenato",
        "description": "Completati 5 quiz.",
        "emoji": "🎯",
        "rarity": "comune",
    },
    "quiz_25": {
        "title": "Guerriero della Conoscenza",
        "description": "Completati 25 quiz.",
        "emoji": "⚔️",
        "rarity": "non comune",
    },
    # Esplorazione
    "food_10": {
        "title": "Gourmet del Sol Levante",
        "description": "Esplorati 10 piatti nella sezione Cibo.",
        "emoji": "🍱",
        "rarity": "comune",
    },
    "places_5": {
        "title": "Viaggiatore Curioso",
        "description": "Visitati 5 luoghi iconici.",
        "emoji": "🗾",
        "rarity": "comune",
    },
    "culture_all": {
        "title": "Anima Nipponica",
        "description": "Esplorati tutti i moduli della sezione Cultura.",
        "emoji": "🌸",
        "rarity": "non comune",
    },
    "history_all": {
        "title": "Studioso della Storia",
        "description": "Letti tutti gli episodi della sezione Storia.",
        "emoji": "🏯",
        "rarity": "non comune",
    },
    # Kanji (per quando sarà implementato)
    "kanji_first": {
        "title": "L'Inizio del Kanji",
        "description": "Completato il primo quiz Kanji.",
        "emoji": "漢",
        "rarity": "non comune",
    },
    "vocab_50": {
        "title": "Dizionario Vivente",
        "description": "Imparate 50 parole di vocabolario.",
        "emoji": "📖",
        "rarity": "raro",
    },
}

RARITY_COLOR: dict[str, str] = {
    "comune":      KotobaTheme.RARITY_COMUNE,
    "non comune":  KotobaTheme.RARITY_NON_COMUNE,
    "raro":        KotobaTheme.RARITY_RARO,
    "epico":       KotobaTheme.RARITY_EPICO,
}
