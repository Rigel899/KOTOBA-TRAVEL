"""
core/app_state.py — Single write point for the current user session.

Both DBManager.current_username and state["user"] track who is logged in.
All login / registration / recovery code paths MUST go through set_user()
to keep the two sources in sync.
"""
from __future__ import annotations
from src.core.db_manager import DBManager


def set_user(state: dict, username: str) -> None:
    """Set the current user in both state dict and DBManager."""
    state["user"] = username
    DBManager.current_username = username
