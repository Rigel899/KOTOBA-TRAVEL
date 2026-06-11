"""
ui/settings_view.py - Profilo e impostazioni account.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import flet as ft

from src.core.db_manager import DBManager
from src.core.app_state import clear_user, get_current_user
from src.core.settings import APP_VERSION, KotobaTheme as T
from src.ui.components.masthead import build_masthead
from src.ui.components.stage import centered_stage


class SettingsView:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        self.user_data = DBManager.get_user_data(self.username) or {}
        self.msg = ft.Text("", size=T.FS_SMALL, color=T.TEXT_M, font_family=T.FONT_BODY)

    def _tf(self, **kwargs) -> ft.TextField:
        return ft.TextField(
            bgcolor=T.BG_SURF,
            border_color=T.BORDER,
            focused_border_color=T.GOLD,
            color=T.TEXT,
            cursor_color=T.GOLD,
            border_radius=T.RADIUS_S,
            height=44,
            text_size=13,
            hint_style=ft.TextStyle(color=T.TEXT_M, font_family=T.FONT_BODY),
            text_style=ft.TextStyle(font_family=T.FONT_BODY, size=T.FS_BODY),
            **kwargs,
        )

    def _button_style(self, bgcolor: str, color: str = T.TEXT) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            bgcolor=bgcolor,
            color=color,
            shape=ft.RoundedRectangleBorder(radius=T.RADIUS_S),
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            elevation=0,
        )

    def _panel(self, title: str, icon, controls: list[ft.Control], accent: str = T.GOLD) -> ft.Control:
        return ft.Container(
            bgcolor=T.BG_CARD,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.all(18),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=accent, size=22),
                            ft.Text(title, size=17, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=4),
                    *controls,
                ],
                spacing=10,
            ),
        )

    def _set_msg(self, text: str, color: str = T.TEXT_M):
        self.msg.value = text
        self.msg.color = color
        self.page.update()

    def _format_profile_date(self, value: str | None) -> str:
        if not value:
            return "non disponibile"
        try:
            return datetime.fromisoformat(value).strftime("%d/%m/%Y %H:%M")
        except (TypeError, ValueError):
            return str(value)

    def _verify_current_password(self, password: str) -> bool:
        if not DBManager.verify_login(self.username, password):
            self._set_msg("Password corrente non corretta.", T.ERR)
            return False
        return True

    def _change_password(self, current_field: ft.TextField, new_field: ft.TextField, confirm_field: ft.TextField):
        current = current_field.value or ""
        new_pwd = new_field.value or ""
        confirm = confirm_field.value or ""

        if not self._verify_current_password(current):
            return
        pwd_error = DBManager.password_validation_error(new_pwd)
        if pwd_error:
            self._set_msg(pwd_error, T.ERR)
            return
        if new_pwd != confirm:
            self._set_msg("Le nuove password non coincidono.", T.ERR)
            return

        data = DBManager.get_user_data(self.username)
        if not data:
            self._set_msg("Profilo non trovato.", T.ERR)
            return
        data["password_hash"] = DBManager.hash_string(new_pwd)
        DBManager.update_user_data(self.username, data)
        current_field.value = ""
        new_field.value = ""
        confirm_field.value = ""
        self._set_msg("Password aggiornata.", T.GREEN)

    def _change_recovery(self, password_field: ft.TextField, question_field: ft.TextField, answer_field: ft.TextField):
        password = password_field.value or ""
        question = (question_field.value or "").strip()
        answer = answer_field.value or ""

        if not self._verify_current_password(password):
            return
        if not question or not answer:
            self._set_msg("Compila domanda e risposta di sicurezza.", T.ERR)
            return

        data = DBManager.get_user_data(self.username)
        if not data:
            self._set_msg("Profilo non trovato.", T.ERR)
            return
        data["recovery_question"] = question
        data["recovery_answer_hash"] = DBManager.hash_string(answer)
        DBManager.update_user_data(self.username, data)
        password_field.value = ""
        question_field.value = ""
        answer_field.value = ""
        self._set_msg("Recupero password aggiornato.", T.GREEN)

    def _export_profile(self):
        export_data = DBManager.export_safe_profile(self.username)
        if not export_data:
            self._set_msg("Profilo non trovato.", T.ERR)
            return

        export_dir = os.path.join(DBManager.user_data_dir(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(export_dir, f"kotoba_profile_{self.username}_{stamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        self._set_msg(f"Profilo esportato in {path}", T.GREEN)

    def _delete_account(self, password_field: ft.TextField, confirm_field: ft.TextField):
        password = password_field.value or ""
        confirm = DBManager.normalize_username(confirm_field.value or "")

        if confirm != self.username:
            self._set_msg("Per eliminare l'account scrivi il tuo nome utente.", T.ERR)
            return
        if not self._verify_current_password(password):
            return

        DBManager.delete_account(self.username)
        clear_user(self.state)
        self.navigate("/")

    def build(self) -> ft.Control:
        if not self.user_data:
            self.navigate("/")
            return ft.Container(expand=True, bgcolor=T.BG_MAIN)

        current_pwd = self._tf(hint_text="Password corrente", password=True, can_reveal_password=True)
        new_pwd = self._tf(hint_text="Nuova password", password=True, can_reveal_password=True)
        confirm_pwd = self._tf(hint_text="Ripeti nuova password", password=True, can_reveal_password=True)

        recovery_pwd = self._tf(hint_text="Password corrente", password=True, can_reveal_password=True)
        recovery_q = self._tf(hint_text="Nuova domanda di sicurezza")
        recovery_a = self._tf(hint_text="Nuova risposta di sicurezza", password=True)

        delete_pwd = self._tf(hint_text="Password corrente", password=True, can_reveal_password=True)
        delete_confirm = self._tf(hint_text=f"Scrivi {self.username} per confermare")

        created_at = self._format_profile_date(self.user_data.get("created_at"))
        last_login = self._format_profile_date(self.user_data.get("last_login"))

        profile_summary = self._panel(
            "Profilo",
            ft.Icons.ACCOUNT_CIRCLE_ROUNDED,
            [
                ft.Text(f"Utente: {self.username}", size=13, color=T.TEXT, font_family=T.FONT_BODY),
                ft.Text(f"Account creato: {created_at}", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                ft.Text(f"Ultimo accesso: {last_login}", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                ft.Text(f"Versione app: v{APP_VERSION}", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                ft.Button(
                    "Esporta profilo",
                    icon=ft.Icons.DOWNLOAD_ROUNDED,
                    style=self._button_style(T.BG_SURF),
                    on_click=lambda e: self._export_profile(),
                ),
            ],
            accent=T.INDIGO,
        )

        password_panel = self._panel(
            "Password",
            ft.Icons.PASSWORD_ROUNDED,
            [
                current_pwd,
                new_pwd,
                confirm_pwd,
                ft.Button(
                    "Aggiorna password",
                    icon=ft.Icons.SAVE_ROUNDED,
                    style=self._button_style(T.GOLD, T.BG_MAIN),
                    on_click=lambda e: self._change_password(current_pwd, new_pwd, confirm_pwd),
                ),
            ],
        )

        recovery_panel = self._panel(
            "Recupero",
            ft.Icons.SECURITY_ROUNDED,
            [
                recovery_pwd,
                recovery_q,
                recovery_a,
                ft.Text("La risposta distingue maiuscole e minuscole.", size=11, color=T.TEXT_M, italic=True, font_family=T.FONT_BODY),
                ft.Button(
                    "Aggiorna recupero",
                    icon=ft.Icons.SAVE_ROUNDED,
                    style=self._button_style(T.GREEN, T.BG_MAIN),
                    on_click=lambda e: self._change_recovery(recovery_pwd, recovery_q, recovery_a),
                ),
            ],
            accent=T.GREEN,
        )

        danger_panel = self._panel(
            "Elimina account",
            ft.Icons.DELETE_FOREVER_ROUNDED,
            [
                ft.Text("Questa azione elimina il profilo locale e non puo essere annullata.", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                delete_pwd,
                delete_confirm,
                ft.Button(
                    "Elimina definitivamente",
                    icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                    style=self._button_style(T.RED),
                    on_click=lambda e: self._delete_account(delete_pwd, delete_confirm),
                ),
            ],
            accent=T.RED,
        )

        content = ft.Column(
            [
                profile_summary,
                ft.Row(
                    [
                        ft.Container(content=password_panel, expand=True),
                        ft.Container(content=recovery_panel, expand=True),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                danger_panel,
                self.msg,
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        masthead = build_masthead(
            title="Impostazioni",
            subtitle="設定 - Settei",
            on_back=lambda e: self.navigate("dashboard"),
        )

        bg_path = T.bg_image()
        dec_image = ft.DecorationImage(src=bg_path, fit=ft.BoxFit.COVER, opacity=T.BG_OPACITY) if bg_path else None

        return ft.Container(
            bgcolor=T.BG_MAIN,
            image=dec_image,
            expand=True,
            content=ft.Column(
                [
                    masthead,
                    ft.Container(content=centered_stage(self.page, content, max_width=980), expand=True, padding=ft.padding.all(24)),
                ],
                spacing=0,
                expand=True,
            ),
        )
