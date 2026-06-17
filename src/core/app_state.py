"""
core/app_state.py — Single write point for the current user session.

Both DBManager.current_username and state["user"] track who is logged in.
All login / registration / recovery code paths MUST go through set_user()
to keep the two sources in sync.
"""
from __future__ import annotations
from src.core.db_manager import DBManager


GUEST_USERNAME = "Viandante"


def set_user(state: dict, username: str) -> None:
    """Set the current user in both state dict and DBManager."""
    state["user"] = username
    DBManager.current_username = username


def clear_user(state: dict) -> None:
    """Clear the current session user in both state dict and DBManager."""
    state.pop("user", None)
    DBManager.current_username = GUEST_USERNAME


def get_current_user(state: dict | None = None) -> str:
    """Return the current session user, preferring the route state."""
    if state:
        username = state.get("user")
        if username:
            return username
    return DBManager.current_username or GUEST_USERNAME


def is_guest(state: dict | None = None) -> bool:
    """Return True when no real account is logged in."""
    return get_current_user(state) == GUEST_USERNAME
