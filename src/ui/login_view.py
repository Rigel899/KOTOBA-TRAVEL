"""
ui/login_view.py – Login con palette sumi-e.
Spazi vuoti azzerati tramite margini negativi per compensare la trasparenza del logo.
"""
import asyncio

import flet as ft
from src.core.settings import KotobaTheme
from src.core.db_manager import DBManager
from src.core.app_state import set_user

T = KotobaTheme

class LoginView:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self._pending_user = ""
        self._pending_pwd  = ""
        self._recovery_data: dict = {}
        self._build_controls()

    def _tf(self, **kw) -> ft.TextField:
        return ft.TextField(
            bgcolor=T.BG_SURF,
            border_color=T.BORDER,
            focused_border_color=T.GOLD,
            color=T.TEXT,
            hint_style=ft.TextStyle(color=T.TEXT_M, font_family=T.FONT_BODY),
            text_style=ft.TextStyle(font_family=T.FONT_BODY, size=T.FS_BODY),
            border_radius=T.RADIUS_S,
            height=44, 
            text_size=13,
            cursor_color=T.GOLD,
            **kw,
        )

    def _btn_style(self, bg, bg_h, fg=None):
        return ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: bg, ft.ControlState.HOVERED: bg_h},
            color=fg or T.TEXT,
            shape=ft.RoundedRectangleBorder(radius=T.RADIUS_S),
            padding=ft.Padding(top=12, bottom=12, left=24, right=24), 
            elevation=0,
            text_style=ft.TextStyle(
                size=T.FS_BODY,
                weight=ft.FontWeight.W_600,
                font_family=T.FONT_BODY,
            ),
        )

    def _build_controls(self):
        self.user_field = self._tf(hint_text="Nome utente (lettere, numeri, _)", on_submit=self._on_login)
        self.pwd_field  = self._tf(hint_text="Password (min. 8 caratteri)", password=True, can_reveal_password=True, on_submit=self._on_login)

        self.reg_label = ft.Text("Nuovo guerriero? Imposta il recupero password:", size=T.FS_SMALL, color=T.TEXT_M, visible=False, font_family=T.FONT_BODY, italic=True)
        self.q_field = self._tf(hint_text="Domanda di sicurezza (es: animale?)", visible=False, on_submit=self._on_register)
        self.a_field = self._tf(hint_text="Risposta segreta", password=True, visible=False, on_submit=self._on_register)

        self.rec_q_label = ft.Text("", size=T.FS_BODY, color=T.GOLD, weight=ft.FontWeight.BOLD, visible=False, font_family=T.FONT_DISPLAY)
        self.rec_ans_field = self._tf(hint_text="Risposta di sicurezza", password=True, visible=False)
        self.new_pwd_field = self._tf(hint_text="Nuova password", password=True, can_reveal_password=True, visible=False, on_submit=self._on_save_password)

        self.msg = ft.Text("", size=T.FS_SMALL, text_align=ft.TextAlign.CENTER, font_family=T.FONT_BODY)

        self.primary_btn = ft.ElevatedButton("Entra / Crea account", style=self._btn_style(T.RED, T.RED_D), on_click=self._on_login)
        self.register_btn = ft.ElevatedButton("Registrati e inizia il cammino →", style=self._btn_style(T.GREEN, T.GREEN_D, fg=T.BG_MAIN), visible=False, on_click=self._on_register)
        self.recover_btn = ft.TextButton("Hai dimenticato la password?", style=ft.ButtonStyle(color=T.GOLD, text_style=ft.TextStyle(font_family=T.FONT_BODY, size=T.FS_SMALL, decoration=ft.TextDecoration.UNDERLINE)), visible=False, on_click=self._on_show_recovery)
        self.verify_btn = ft.ElevatedButton("Verifica risposta", style=self._btn_style(T.BG_SURF, T.BG_HOVER), visible=False, on_click=self._on_verify_recovery)
        self.save_pwd_btn = ft.ElevatedButton("Salva e accedi →", style=self._btn_style(T.GREEN, T.GREEN_D, fg=T.BG_MAIN), visible=False, on_click=self._on_save_password)

    def _safe_page_update(self):
        try:
            self.page.update()
        except RuntimeError:
            pass

    async def _cooldown_login(self, delay: float | None = None):
        await asyncio.sleep(delay if delay is not None else DBManager.LOCKOUT_SECONDS)
        self.primary_btn.disabled = False
        self._show_msg("Puoi riprovare ad accedere.", T.TEXT_M)
        self._safe_page_update()

    async def _cooldown_recovery(self, delay: float | None = None):
        await asyncio.sleep(delay if delay is not None else DBManager.LOCKOUT_SECONDS)
        self.verify_btn.disabled = False
        self._show_msg("Puoi riprovare il recupero password.", T.TEXT_M)
        self._safe_page_update()

    def _start_login_cooldown(self):
        self.primary_btn.disabled = True
        self._show_msg("Troppi tentativi. Riprova tra 30 secondi.", T.ERR)
        self.page.run_task(self._cooldown_login)

    def _start_recovery_cooldown(self):
        self.verify_btn.disabled = True
        self._show_msg("Troppi tentativi. Riprova tra 30 secondi.", T.ERR)
        self.page.run_task(self._cooldown_recovery)

    def _on_login(self, e=None):
        raw_user = self.user_field.value.strip()
        user = DBManager.normalize_username(raw_user)
        pwd  = self.pwd_field.value or ""
        self._clear_errors()
        user_error = DBManager.username_validation_error(raw_user)
        if user_error:
            self.user_field.border_color = T.ERR
            self._show_msg(user_error, T.ERR)
            self.page.update(); return
        if not pwd:
            self._show_msg("Inserisci nome utente e password.", T.ERR)
            self.page.update(); return
        pwd_error = DBManager.password_validation_error(pwd)
        if pwd_error:
            self.pwd_field.border_color = T.ERR
            self._show_msg(pwd_error, T.ERR)
            self.page.update(); return
        if raw_user != user:
            self.user_field.value = user

        if DBManager.user_exists(user):
            is_locked, remaining_secs = DBManager.is_locked_out(user, "login")
            if is_locked:
                self.primary_btn.disabled = True
                self._show_msg(f"Troppi tentativi. Riprova tra {remaining_secs} secondi.", T.ERR)
                self.page.run_task(self._cooldown_login, remaining_secs)
                self.page.update()
                return
            if DBManager.verify_login(user, pwd):
                DBManager.clear_failed_attempts(user, "login")
                set_user(self.state, user)
                import datetime
                data = DBManager.get_user_data(user) or {}
                data["last_login"] = datetime.datetime.now().isoformat()
                DBManager.update_user_data(user, data)
                self.navigate("dashboard")
            else:
                self.pwd_field.border_color = T.ERR
                self._pending_user = user
                if DBManager.record_failed_attempt(user, "login"):
                    self._start_login_cooldown()
                else:
                    remaining = DBManager.remaining_attempts(user, "login")
                    self._show_msg(f"Password errata. Tentativi rimasti: {remaining}.", T.ERR)
                self.recover_btn.visible = True
                self.page.update()
        else:
            self._pending_user = user
            self._pending_pwd  = pwd
            self._show_msg(f"Benvenuto, {user}. Crea il tuo account.", T.GOLD)
            self.reg_label.visible    = True
            self.q_field.visible      = True
            self.a_field.visible      = True
            self.register_btn.visible = True
            self.primary_btn.visible  = False
            self.page.update()

    def _on_register(self, e=None):
        if not self._pending_user:
            raw_user = self.user_field.value.strip()
            user_error = DBManager.username_validation_error(raw_user)
            if user_error:
                self.user_field.border_color = T.ERR
                self._show_msg(user_error, T.ERR)
                self.page.update(); return
            self._pending_user = DBManager.normalize_username(raw_user)
        if not self._pending_pwd:
            pwd = self.pwd_field.value or ""
            pwd_error = DBManager.password_validation_error(pwd)
            if pwd_error:
                self.pwd_field.border_color = T.ERR
                self._show_msg(pwd_error, T.ERR)
                self.page.update(); return
            self._pending_pwd = pwd

        q = self.q_field.value.strip()
        a = self.a_field.value.strip()
        if not q or not a:
            self._show_msg("Completa la domanda e la risposta.", T.ERR)
            self.page.update(); return
        try:
            DBManager.create_account(self._pending_user, self._pending_pwd, q, a)
        except ValueError as exc:
            self._show_msg(str(exc), T.ERR)
            self.page.update(); return
        self._pending_pwd = ""
        set_user(self.state, self._pending_user)
        DBManager.unlock_achievement(self._pending_user, "first_steps")
        self.state["just_registered"] = True
        self.navigate("dashboard")

    def _on_show_recovery(self, e=None):
        data = DBManager.get_user_data(self._pending_user)
        if not data: return
        self._recovery_data = {
            "username": self._pending_user,
            "recovery_question": data.get("recovery_question", ""),
            "recovery_answer_hash": data.get("recovery_answer_hash", ""),
        }
        self.recover_btn.visible   = False
        question = self._recovery_data.get("recovery_question", "Domanda")
        self.rec_q_label.value     = f"?  {question}"
        self.rec_q_label.visible   = True
        self.rec_ans_field.visible = True
        self.verify_btn.visible    = True
        self._show_msg("Rispondi alla domanda di sicurezza.", T.TEXT_M)
        self.page.update()

    def _on_verify_recovery(self, e=None):
        pending_username = self._recovery_data.get("username", "")
        is_locked, remaining_secs = DBManager.is_locked_out(pending_username, "recovery")
        if is_locked:
            self.verify_btn.disabled = True
            self._show_msg(f"Troppi tentativi. Riprova tra {remaining_secs} secondi.", T.ERR)
            self.page.run_task(self._cooldown_recovery, remaining_secs)
            self.page.update()
            return

        ans = self.rec_ans_field.value.strip()
        stored_hash = self._recovery_data.get("recovery_answer_hash", "")
        if DBManager.verify_secret(ans, stored_hash):
            DBManager.clear_failed_attempts(pending_username, "recovery")
            if DBManager.is_legacy_hash(ans, stored_hash):
                self._recovery_data["recovery_answer_hash"] = DBManager.hash_string(ans)
            self.rec_ans_field.border_color = T.GREEN
            self.rec_ans_field.read_only    = True
            self.verify_btn.visible         = False
            self.new_pwd_field.visible      = True
            self.save_pwd_btn.visible       = True
            self._show_msg("Risposta corretta. Imposta la nuova password.", T.GREEN)
        else:
            self.rec_ans_field.border_color = T.ERR
            if DBManager.record_failed_attempt(pending_username, "recovery"):
                self._start_recovery_cooldown()
            else:
                remaining = DBManager.remaining_attempts(pending_username, "recovery")
                self._show_msg(f"Risposta errata. Tentativi rimasti: {remaining}.", T.ERR)
        self.page.update()

    def _on_save_password(self, e=None):
        new_pwd = self.new_pwd_field.value or ""
        pwd_error = DBManager.password_validation_error(new_pwd)
        if pwd_error:
            self.new_pwd_field.border_color = T.ERR
            self._show_msg(pwd_error, T.ERR)
            self.page.update(); return
        data = DBManager.get_user_data(self._pending_user)
        if not data:
            self._show_msg("Impossibile aggiornare il profilo.", T.ERR)
            self.page.update(); return
        data["password_hash"] = DBManager.hash_string(new_pwd)
        if self._recovery_data.get("recovery_answer_hash"):
            data["recovery_answer_hash"] = self._recovery_data["recovery_answer_hash"]
        DBManager.update_user_data(self._pending_user, data)
        set_user(self.state, self._pending_user)
        self._recovery_data = {}
        self.navigate("dashboard")

    def _clear_errors(self):
        self.user_field.border_color = T.BORDER
        self.pwd_field.border_color  = T.BORDER
        self.msg.value = ""

    def _show_msg(self, text: str, color: str):
        self.msg.value = text
        self.msg.color = color

    # ── build ────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        img = ft.Image(
            src=T.asset_path("image/icons/icona.png"),
            width=132,
            height=132,
            fit=ft.BoxFit.CONTAIN,
            error_content=ft.Text("⛩", size=100, color=T.GOLD, text_align=ft.TextAlign.CENTER),
        )

        logo = ft.Container(
            content=img,
            margin=ft.Margin(left=0, top=14, right=0, bottom=4)
        )

        title_block = ft.Column([
            ft.Text("Kotoba Travel", size=26, weight=ft.FontWeight.W_700, color=T.TEXT, font_family=T.FONT_DISPLAY),
            ft.Text("ことば旅", size=16, color=T.GOLD, italic=True, font_family=T.FONT_DISPLAY),
            ft.Text("Il tuo viaggio in Giappone", size=13, color=T.TEXT_M, font_family=T.FONT_BODY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

        header = ft.Column([
            logo,
            title_block
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

        form = ft.Column([
            self.user_field,
            self.pwd_field,
            self.reg_label,
            self.q_field,
            self.a_field,
            self.rec_q_label,
            self.rec_ans_field,
            self.new_pwd_field,
            self.msg,
            self.primary_btn,
            self.register_btn,
            self.recover_btn,
            self.verify_btn,
            self.save_pwd_btn,
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        card = ft.Container(
            content=ft.Column([
                header,
                ft.Container(height=16),
                form,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.BORDER),
            padding=ft.Padding(top=8, bottom=24, left=36, right=36),
            width=420,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=50, 
                color=ft.Colors.with_opacity(0.4, "#000000"),
                offset=ft.Offset(0, 10),
            ),
        )

        kwargs = dict(
            expand=True,
            bgcolor=T.BG_MAIN,
            alignment=ft.Alignment(0, 0),
            padding=ft.padding.symmetric(vertical=16, horizontal=20)
        )
        bg_img = T.bg_image()
        if bg_img:
            kwargs["image_src"] = bg_img
            kwargs["image_fit"] = ft.BoxFit.COVER
            kwargs["image_opacity"] = T.BG_OPACITY

        return ft.Container(
            content=ft.Column(
                [card], 
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
            ), 
            **kwargs
        )
