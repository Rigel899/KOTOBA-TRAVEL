"""
core/settings.py – Temi "Viola Murasaki" (scuro) e "Washi" (chiaro) per Kotoba Travel.
Palette ispirata all'estetica giapponese premium:
  murasaki 紫   – viola profondo, sfondo notturno
  washi    和紙 – carta riso, sfondo diurno
  glicine  藤   – wisteria (#C9A0DC), accento principale
  kin      金   – oro (#D4AF37), evidenze kintsugi
"""
import os


APP_VERSION = "1.0.0"


class KotobaTheme:
    _bg_image_cache: str | None = None
    _bg_image_loaded = False
    _current = "murasaki"
    IS_DARK = True

    # ── Palette disponibili ─────────────────────────────────────────────────
    THEMES: dict = {
        "murasaki": {
            "IS_DARK":           True,
            "BG_MAIN":          "#1E1630",
            "BG_CARD":          "#272040",
            "BG_SURF":          "#302848",
            "BG_HOVER":         "#3A3058",
            "BG_INK":           "#160F28",
            "BORDER":           "#3D3060",
            "BORDER_F":         "#D4AF37",
            "TEXT":             "#EDE8FF",
            "TEXT_M":           "#8870B0",
            "RED":              "#D14A3F",
            "RED_D":            "#B23E33",
            "GREEN":            "#7FA88F",
            "GREEN_D":          "#5E8870",
            "GOLD":             "#D4AF37",
            "INDIGO":           "#7090C0",
            "INDIGO_D":         "#1B3B6F",
            "INDIGO_H":         "#5878B0",
            "PURPLE":           "#DDB8EE",
            "ERR":              "#E5544A",
            "BELT_KANA":        "#C87840",
            "BELT_KANJI":       "#D85040",
            "BELT_VOCAB":       "#7090D0",
            "BELT_GRAMMAR":     "#50C090",
            "BELT_CULTURE":     "#50C090",
            "BELT_ACCADEMIA":   "#E07898",
            "BELT_MASTER":      "#D4AF5C",
            "BELT_MASTER_HOVER":"#C8A030",
            "BELT_MASTER_EDGE": "#BF9818",
            "RARITY_SILVER":    "#C7CCD4",
            "RARITY_BRONZE":    "#B8793C",
            "RARITY_WOOD":      "#8B5E3C",
            "RARITY_PLATINO":   "#C7ECFF",
            "QUIZ_CORRECT_BG":     "#1A3A1A",
            "QUIZ_CORRECT_BORDER": "#58C858",
            "QUIZ_WRONG_BG":       "#3D1414",
            "BG_OPACITY":       0.10,
        },
        "fuji": {
            "IS_DARK":           False,
            "BG_MAIN":          "#ECE4F6",
            "BG_CARD":          "#F6F0FE",
            "BG_SURF":          "#E3D8F2",
            "BG_HOVER":         "#D8CBEE",
            "BG_INK":           "#F9F5FF",
            "BORDER":           "#C8B4E8",
            "BORDER_F":         "#C8A010",
            "TEXT":             "#1E1030",
            "TEXT_M":           "#8060A8",
            "RED":              "#D82820",
            "RED_D":            "#B01A14",
            "GREEN":            "#3D6E52",
            "GREEN_D":          "#2D5440",
            "GOLD":             "#C8A010",
            "INDIGO":           "#5C7EC0",
            "INDIGO_D":         "#D8E4F5",
            "INDIGO_H":         "#4A6BA8",
            "PURPLE":           "#7B52A8",
            "ERR":              "#C23B30",
            "BELT_KANA":        "#C07840",
            "BELT_KANJI":       "#D82820",
            "BELT_VOCAB":       "#5070C0",
            "BELT_GRAMMAR":     "#289878",
            "BELT_CULTURE":     "#289878",
            "BELT_ACCADEMIA":   "#D84080",
            "BELT_MASTER":      "#C8A010",
            "BELT_MASTER_HOVER":"#B89000",
            "BELT_MASTER_EDGE": "#A87800",
            "RARITY_SILVER":    "#7878A0",
            "RARITY_BRONZE":    "#9B6028",
            "RARITY_WOOD":      "#6B4028",
            "RARITY_PLATINO":   "#4878A0",
            "QUIZ_CORRECT_BG":     "#D4F5E4",
            "QUIZ_CORRECT_BORDER": "#3A9870",
            "QUIZ_WRONG_BG":       "#F5D4D8",
            "BG_OPACITY":       0.05,
        },
    }

    # ── Sfondi (default = murasaki) ─────────────────────────────────────────
    BG_MAIN   = "#1E1630"
    BG_CARD   = "#272040"
    BG_SURF   = "#302848"
    BG_HOVER  = "#3A3058"
    BG_INK    = "#160F28"

    # ── Bordi ──────────────────────────────────────────────────────────────
    BORDER    = "#3D3060"
    BORDER_F  = "#D4AF37"

    # ── Testo ──────────────────────────────────────────────────────────────
    TEXT      = "#EDE8FF"
    TEXT_M    = "#8870B0"

    # ── Accenti ────────────────────────────────────────────────────────────
    RED       = "#D14A3F"
    RED_D     = "#B23E33"
    GREEN     = "#7FA88F"
    GREEN_D   = "#5E8870"
    GOLD      = "#D4AF37"
    INDIGO    = "#7090C0"
    INDIGO_D  = "#1B3B6F"
    INDIGO_H  = "#5878B0"
    PURPLE    = "#DDB8EE"
    ERR       = "#E5544A"

    # Colori sezione per Dojo, quiz e percorsi di studio.
    BELT_KANA         = "#C87840"
    BELT_KANJI        = "#D85040"
    BELT_VOCAB        = "#7090D0"
    BELT_GRAMMAR      = "#50C090"
    BELT_CULTURE      = "#50C090"
    BELT_ACCADEMIA    = "#E07898"
    BELT_MASTER       = "#D4AF5C"
    BELT_MASTER_HOVER = "#C8A030"
    BELT_MASTER_EDGE  = "#BF9818"

    # Achievement rarity colors
    RARITY_COMUNE      = "#EDE8FF"
    RARITY_RARO        = "#7FA88F"
    RARITY_MOLTO_RARO  = "#7090C0"
    RARITY_EPICO       = "#C9A0DC"
    RARITY_LEGGENDARIO = "#D4AF37"
    RARITY_PLATINO     = "#C7ECFF"
    RARITY_SILVER      = "#C7CCD4"
    RARITY_BRONZE      = "#B8793C"
    RARITY_WOOD        = "#8B5E3C"

    # Quiz feedback colors
    QUIZ_CORRECT_BG     = "#1A3A22"
    QUIZ_CORRECT_BORDER = "#34D399"
    QUIZ_WRONG_BG       = "#3D1414"

    @classmethod
    def apply_theme(cls, name: str) -> None:
        """Applica la palette indicata aggiornando tutte le class var."""
        palette = cls.THEMES.get(name, cls.THEMES["murasaki"])
        for attr, value in palette.items():
            setattr(cls, attr, value)
        cls._current = name
        # Aggiorna le costanti derivate dai colori base
        cls.RARITY_COMUNE = cls.TEXT
        cls.RARITY_RARO = cls.GREEN
        cls.RARITY_MOLTO_RARO = cls.INDIGO
        cls.RARITY_EPICO = cls.PURPLE
        cls.RARITY_LEGGENDARIO = cls.GOLD
        cls._bg_image_loaded = False

    @staticmethod
    def os_preferred_theme() -> str:
        """Legge il tema preferito dal sistema operativo (Windows)."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "fuji" if value == 1 else "murasaki"
        except Exception:
            return "murasaki"

    @staticmethod
    def _app_settings_path() -> str:
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(appdata, "Kotoba", "app_settings.json")

    @classmethod
    def load_app_theme(cls) -> str:
        """Carica la preferenza tema dall'app; default murasaki."""
        try:
            import json
            path = cls._app_settings_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pref = data.get("theme", "murasaki")
                if pref == "sistema":
                    return cls.os_preferred_theme()
                if pref in cls.THEMES:
                    return pref
        except Exception:
            pass
        return "murasaki"

    @classmethod
    def save_app_theme(cls, name: str) -> None:
        """Salva la preferenza tema globale (include 'sistema')."""
        try:
            import json
            path = cls._app_settings_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"theme": name}, f)
        except Exception:
            pass

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
