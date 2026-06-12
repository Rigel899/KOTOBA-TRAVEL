"""
core/compat.py  –  Shim per Flet >= 0.80
Importato UNA VOLTA in main.py prima di tutto il resto.
Ripristina le vecchie API helper rimosse nella 0.80+:
  ft.border.all / ft.border.only
  ft.padding.symmetric / ft.padding.all / ft.padding.only  (backup)
  ft.margin.symmetric / ft.margin.all / ft.margin.only     (backup)
"""
import flet as ft

# ── border ────────────────────────────────────────────────────────────────────

def _border_all(width: float = 1, color=None):
    s = ft.BorderSide(width=width, color=color)
    return ft.Border(top=s, right=s, bottom=s, left=s)

def _border_only(top=None, right=None, bottom=None, left=None):
    return ft.Border(top=top, right=right, bottom=bottom, left=left)

# Creazione sicura dello spazio dei nomi se il modulo è stato rimosso
class _BorderNamespace:
    pass

if not hasattr(ft, "border"):
    ft.border = _BorderNamespace()

if not hasattr(ft.border, "all"):
    ft.border.all = _border_all
    ft.border.only = _border_only


# ── padding (backup per casi residui) ────────────────────────────────────────

class _PaddingHelper:
    @staticmethod
    def all(v):
        # Corretto: Assegnazione esplicita a tutti e 4 i lati
        return ft.Padding(left=v, top=v, right=v, bottom=v)
        
    @staticmethod
    def symmetric(vertical=0, horizontal=0):
        return ft.Padding(top=vertical, bottom=vertical,
                          left=horizontal, right=horizontal)
                          
    @staticmethod
    def only(left=0, top=0, right=0, bottom=0):
        return ft.Padding(left=left, top=top, right=right, bottom=bottom)

if not hasattr(ft, "padding") or not hasattr(ft.padding, "all"):
    ft.padding = _PaddingHelper()


# ── margin (backup) ───────────────────────────────────────────────────────────

class _MarginHelper:
    @staticmethod
    def all(v):
        # Corretto: Assegnazione esplicita a tutti e 4 i lati
        return ft.Margin(left=v, top=v, right=v, bottom=v)
        
    @staticmethod
    def symmetric(vertical=0, horizontal=0):
        return ft.Margin(top=vertical, bottom=vertical,
                         left=horizontal, right=horizontal)
                         
    @staticmethod
    def only(left=0, top=0, right=0, bottom=0):
        return ft.Margin(left=left, top=top, right=right, bottom=bottom)

if not hasattr(ft, "margin") or not hasattr(ft.margin, "all"):
    ft.margin = _MarginHelper()


# ── colors / icons alias (Flet 0.80+ rinomina da minuscolo a maiuscolo) ───────

if not hasattr(ft, "colors"):
    ft.colors = ft.Colors

if not hasattr(ft, "icons"):
    ft.icons = ft.Icons


# ── snackbar / dialog helpers ─────────────────────────────────────────────────

def show_snack(page: ft.Page, snack: ft.SnackBar) -> None:
    """Mostra uno SnackBar compatibile con Flet 0.80+ e versioni precedenti."""
    try:
        page.open(snack)
    except AttributeError:
        page.snack_bar = snack
        snack.open = True
        page.update()


def open_dialog(page: ft.Page, dialog) -> None:
    """Apre un dialogo compatibile con Flet 0.80+ e versioni precedenti."""
    try:
        page.open(dialog)
    except AttributeError:
        page.dialog = dialog
        dialog.open = True
        page.update()


def close_dialog(page: ft.Page, dialog) -> None:
    """Chiude un dialogo compatibile con Flet 0.80+ e versioni precedenti."""
    try:
        page.close(dialog)
    except AttributeError:
        dialog.open = False
        page.update()