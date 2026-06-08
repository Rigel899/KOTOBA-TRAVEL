"""
ui/components/loader.py
Componenti riutilizzabili:
  - TrainProgress: barra progresso animata con treno 🚄 per i quiz
  - show_achievement: popup toast quando si sblocca un achievement
"""

import flet as ft
from src.core.settings import KotobaTheme


# ─────────────────────────────────────────────────────────────────────────────
# TrainProgress
# ─────────────────────────────────────────────────────────────────────────────

class TrainProgress:
    """
    Barra progresso tematizzata per i quiz.
    Il treno 🚄 avanza lungo il binario ad ogni domanda completata.

    Uso:
        tp = TrainProgress(page, total_steps=10)
        column.controls.append(tp.build())
        ...
        tp.advance()   # chiama page.update() automaticamente
    """

    def __init__(self, page: ft.Page, total_steps: int, track_width: int = 480,
                 stations: list[str] | None = None,
                 header: str = "🗾  Percorso"):
        self.page = page
        self.total = max(total_steps, 1)
        self.step = 0
        self.tw = track_width
        self._stations_labels = stations
        self._header = header

        # ── Controlli interni ─────────────────────────────────────────────
        self._fill = ft.Container(
            width=0, height=6,
            bgcolor=KotobaTheme.RED,
            border_radius=3,
            animate=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
        )

        # scale_x=-1 specchia l'emoji così il treno guarda a destra →
        self._train = ft.Container(
            content=ft.Text("🚄", size=22),
            width=28, height=28,
            alignment=ft.Alignment(0, 0),
            transform=ft.Scale(scale_x=-1, scale_y=1),
            top=0, left=0,
            animate=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
        )

        self._label = ft.Text(
            f"0 / {self.total}",
            color=KotobaTheme.GOLD,
            size=KotobaTheme.FS_SMALL,
            weight=ft.FontWeight.BOLD,
        )

    def build(self) -> ft.Control:
        n_stations = min(self.total, 10)

        track_line = ft.Container(
            top=11, left=0, width=self.tw, height=6,
            bgcolor=KotobaTheme.BORDER, border_radius=3,
        )

        # Wrapper fill: dimensioni esplicite ma senza clip_behavior
        # (clip_behavior su Container senza bgcolor crea layer Material bianco in Flet 0.85)
        fill_wrapper = ft.Container(
            top=11, left=0, width=self.tw, height=6,
            content=self._fill,
        )

        # Pallini stazione: ricreati ad ogni build (controlli statici, nessuno stato)
        dot_controls = [
            ft.Container(
                top=11,
                left=int((self.tw - 6) * i / max(n_stations - 1, 1)),
                width=6, height=6,
                bgcolor=KotobaTheme.BORDER_F, border_radius=3,
            )
            for i in range(n_stations)
        ]

        # Container con dimensioni esplicite → Stack riceve vincoli tight → non si espande
        # Nessun clip_behavior: evita layer Material bianco su sfondo trasparente
        track_section = ft.Container(
            width=self.tw,
            height=28,
            content=ft.Stack(
                controls=[track_line, fill_wrapper, *dot_controls, self._train],
            ),
        )

        header_row = ft.Row(
            [
                ft.Text(self._header, color=KotobaTheme.TEXT_M, size=KotobaTheme.FS_SMALL),
                ft.Container(expand=True),
                self._label,
            ],
            width=self.tw,
        )

        col_controls: list[ft.Control] = [header_row, track_section]

        # Nomi città in uno Stack separato sotto la rotaia
        if self._stations_labels:
            lw = 52  # abbastanza largo per "Shinagawa" / "Hiroshima" in romaji
            label_containers = []
            for i, city in enumerate(self._stations_labels[:n_stations]):
                sx = int((self.tw - 6) * i / max(n_stations - 1, 1))
                lx = max(0, min(sx + 3 - lw // 2, self.tw - lw))
                label_containers.append(
                    ft.Container(
                        left=lx, top=0, width=lw, height=14,
                        content=ft.Text(
                            city, size=9,
                            color=KotobaTheme.TEXT_M,
                            font_family=KotobaTheme.FONT_JP,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                )
            col_controls.append(
                ft.Stack(width=self.tw, height=14, controls=label_containers)
            )

        return ft.Column(
            col_controls,
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # ── Metodi pubblici ───────────────────────────────────────────────────

    def advance(self) -> None:
        """Avanza di un passo e aggiorna la UI."""
        self.step = min(self.step + 1, self.total)
        self._refresh()

    def set_step(self, step: int) -> None:
        self.step = max(0, min(step, self.total))
        self._refresh()

    def reset(self) -> None:
        self.step = 0
        self._refresh()

    # ── Interno ───────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        ratio = self.step / self.total
        fill_px = int(self.tw * ratio)
        train_left = max(0, int((self.tw - 28) * ratio))

        self._fill.width = fill_px
        self._train.left = train_left
        self._label.value = f"{self.step} / {self.total}"
        self.page.update()


# ─────────────────────────────────────────────────────────────────────────────
# Achievement toast
# ─────────────────────────────────────────────────────────────────────────────

def show_achievement(page: ft.Page, ach_data: dict) -> None:
    """
    Mostra un toast/snackbar stilizzato quando si sblocca un achievement.

    Parametri:
        page     – la pagina Flet corrente
        ach_data – dizionario dell'achievement da core.achievements.ACHIEVEMENTS
    """
    from src.core.achievements import RARITY_COLOR
    rarity = ach_data.get("rarity", "comune")
    accent = RARITY_COLOR.get(rarity, KotobaTheme.TEXT_M)
    emoji  = ach_data.get("emoji", "🏆")
    title  = ach_data.get("title", "Achievement sbloccato!")
    desc   = ach_data.get("description", "")

    page.snack_bar = ft.SnackBar(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(emoji, size=28),
                    width=44, height=44,
                    bgcolor=KotobaTheme.BG_SURF,
                    border_radius=10,
                    border=ft.border.all(1, accent),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column(
                    [
                        ft.Text(
                            f"🏆  {title}",
                            color=accent,
                            size=13,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(desc, color=KotobaTheme.TEXT_M, size=11),
                    ],
                    spacing=2,
                    tight=True,
                ),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=KotobaTheme.BG_CARD,
        duration=4000,
        show_close_icon=True,
        close_icon_color=KotobaTheme.TEXT_M,
    )
    page.snack_bar.open = True
    page.update()


def show_achievements(page: ft.Page, achievement_ids: list[str]) -> None:
    """Mostra un toast per uno o piu achievement appena sbloccati."""
    if not achievement_ids:
        return
    from src.core.achievements import ACHIEVEMENTS

    unlocked = [ACHIEVEMENTS[ach_id] for ach_id in achievement_ids if ach_id in ACHIEVEMENTS]
    if not unlocked:
        return
    if len(unlocked) == 1:
        show_achievement(page, unlocked[0])
        return

    titles = ", ".join(item.get("title", "Trofeo") for item in unlocked[:3])
    if len(unlocked) > 3:
        titles += f" +{len(unlocked) - 3}"
    show_achievement(
        page,
        {
            "title": f"{len(unlocked)} trofei sbloccati",
            "description": titles,
            "emoji": "🏆",
            "rarity": "epico",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helper per card hover generica
# ─────────────────────────────────────────────────────────────────────────────

