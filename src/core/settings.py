"""
core/settings.py – Tema "Sumi-e" per Kotoba Travel.
Palette ispirata ai pigmenti tradizionali giapponesi, versione notturna:
  sumi  墨    – inchiostro caldo, sfondo
  washi 和紙  – carta riso, testo
  ai    藍    – indaco, struttura
  shu   朱    – vermillion, CTA
  kincha 金茶 – oro spento, evidenze
  matcha 抹茶 – verde tè, conferme
"""
import os


APP_VERSION = "1.0.0"


class KotobaTheme:
    _bg_image_cache: str | None = None
    _bg_image_loaded = False

    # ── Sfondi ─────────────────────────────────────────────────────────────
    BG_MAIN   = "#1C1815"
    BG_CARD   = "#2A2520"
    BG_SURF   = "#332D27"
    BG_HOVER  = "#3A332C"
    BG_INK    = "#0F0D0B"

    # ── Bordi ──────────────────────────────────────────────────────────────
    BORDER    = "#403832"
    BORDER_F  = "#D4AF5C"

    # ── Testo ──────────────────────────────────────────────────────────────
    TEXT      = "#F2EBDF"
    TEXT_M    = "#A99F92"

    # ── Accenti ────────────────────────────────────────────────────────────
    RED       = "#D14A3F"
    RED_D     = "#B23E33"
    GREEN     = "#7FA88F"
    GREEN_D   = "#5E8870"
    GOLD      = "#D4AF5C"
    INDIGO    = "#7090C0"
    INDIGO_D  = "#1B3B6F"
    ERR       = "#E5544A"

    # Colori cintura per Dojo, quiz e percorsi di studio.
    BELT_KANA         = "#E6C83A"  # giallo, non oro
    BELT_KANJI        = GREEN
    BELT_VOCAB        = INDIGO
    BELT_GRAMMAR      = "#A66F45"
    BELT_MASTER       = "#080706"
    BELT_MASTER_HOVER = "#0D0B09"
    BELT_MASTER_EDGE  = "#0A0908"

    # Achievement rarity colors
    RARITY_COMUNE      = TEXT_M
    RARITY_NON_COMUNE  = GREEN
    RARITY_RARO        = INDIGO
    RARITY_EPICO       = GOLD

    # ── Tipografia ─────────────────────────────────────────────────────────
    FONT_DISPLAY = "Shippori Mincho"
    FONT_BODY    = "Inter"
    FONT_JP      = "Noto Sans JP"

    # ── Geometria ──────────────────────────────────────────────────────────
    RADIUS    = 8
    RADIUS_S  = 6

    # ── Dimensioni testo ───────────────────────────────────────────────────
    FS_TITLE  = 28
    FS_H2     = 18
    FS_BODY   = 13
    FS_SMALL  = 11
    FS_TINY   = 10

    # ── Texture di sfondo opzionale ────────────────────────────────────────
    # Metti un file washi.png / paper.png / bg.png / texture.png
    # in asset/image/backgrounds/ e verrà applicato come overlay.
    @staticmethod
    def asset_path(path: str | None) -> str | None:
        if not path:
            return path
        if path.startswith(("http://", "https://", "data:")):
            return path
        return path.replace("\\", "/").lstrip("/")

    @staticmethod
    def bg_image() -> str | None:
        if KotobaTheme._bg_image_loaded:
            return KotobaTheme._bg_image_cache

        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base = os.path.join(app_root, "asset", "image", "backgrounds")
        candidates = (
            "washi.png", "washi.jpg",
            "paper.png", "paper.jpg",
            "bg.png", "bg.jpg",
            "texture.png", "texture.jpg",
        )
        for name in candidates:
            if os.path.exists(os.path.join(base, name)):
                KotobaTheme._bg_image_cache = KotobaTheme.asset_path(f"image/backgrounds/{name}")
                KotobaTheme._bg_image_loaded = True
                return KotobaTheme._bg_image_cache
        KotobaTheme._bg_image_cache = None
        KotobaTheme._bg_image_loaded = True
        return None

    BG_OPACITY = 0.10
