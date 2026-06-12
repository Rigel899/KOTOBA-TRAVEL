"""
core/content_store.py
Caricamento e validazione dei JSON statici dell'app.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from collections.abc import Callable


_log = logging.getLogger("kotoba.content")


class ContentStore:
    _lock: threading.Lock = threading.Lock()

    REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
        "sillabari.json": ("word", "pronunciation", "category", "group"),
        "kanji.json": ("word", "reading", "meaning", "group"),
        "vocabolario.json": ("word", "reading", "meaning", "category", "group"),
        "grammatica.json": ("title", "emoji", "explanation", "example"),
        "food.json": ("word", "pronunciation", "meaning", "category", "description"),
        "explore.json": ("category", "name", "jp", "city", "description", "detail", "tag"),
        "museums.json": ("category", "name", "jp", "city", "description", "detail", "tag"),
        "culture.json": ("title", "subtitle", "content", "category"),
        "history.json": ("title", "subtitle", "content", "period"),
    }
    OPTIONAL_TEXT_FIELDS: dict[str, tuple[str, ...]] = {
        "food.json": ("image", "story", "recipe"),
        "vocabolario.json": ("example",),
    }
    OPTIONAL_LIST_FIELDS: dict[str, tuple[str, ...]] = {
        "food.json": ("allergens",),
    }
    ALLOWED_VALUES: dict[str, dict[str, set[str]]] = {
        "sillabari.json": {
            "category": {"Hiragana", "Katakana"},
        },
        "food.json": {
            "category": {"Primo", "Pesce", "Fritto", "Zuppa", "Street food", "Carne", "Dolce", "Bevanda"},
        },
        "explore.json": {
            "category": {"Giappone Moderno", "Giappone Antico", "Lavori Tipici"},
        },
        "museums.json": {
            "category": {"Musei"},
        },
        "culture.json": {
            "category": {
                "Lingua e scrittura",
                "Studio pratico",
                "Societa e abitudini",
                "Tradizioni e stagioni",
                "Cultura quotidiana",
            },
        },
        "history.json": {
            "period": {
                "Panoramica",
                "Origini",
                "Corte e Stato",
                "Eta samuraica",
                "Edo e contatti",
                "Modernizzazione",
                "Novecento e oggi",
                "Popoli e regioni",
            },
        },
    }
    IMAGE_FIELDS: dict[str, tuple[str, ...]] = {
        "food.json": ("image",),
    }

    def __init__(
        self,
        data_dir: Callable[[], str],
        cache: dict[str, tuple[int, object]] | None = None,
    ) -> None:
        self._data_dir = data_dir
        self._cache = cache if cache is not None else {}

    def _iter_items(self, filename: str, data: object) -> list[dict] | None:
        basename = os.path.basename(filename)
        if isinstance(data, list):
            return data
        if basename in {"culture.json", "history.json"} and isinstance(data, dict):
            topics = data.get("topics")
            if isinstance(topics, list):
                return topics
        return None

    def _validate_text_field(self, filename: str, index: int, item: dict, field: str, *, required: bool) -> bool:
        value = item.get(field)
        if value is None or value == "":
            if required:
                _log.warning("json schema invalid for %s[%s]: missing %s", filename, index, field)
                return False
            return True
        if not isinstance(value, str):
            _log.warning("json schema invalid for %s[%s].%s: expected string", filename, index, field)
            return False
        if required and not value.strip():
            _log.warning("json schema invalid for %s[%s]: empty %s", filename, index, field)
            return False
        return True

    def _validate_allowed_value(self, filename: str, index: int, item: dict, field: str, allowed: set[str]) -> bool:
        value = item.get(field)
        if value not in allowed:
            _log.warning("json schema invalid for %s[%s].%s: unsupported value %r", filename, index, field, value)
            return False
        return True

    def _validate_list_field(self, filename: str, index: int, item: dict, field: str) -> bool:
        if field not in item or item[field] is None:
            return True
        value = item[field]
        if not isinstance(value, list) or any(not isinstance(entry, str) or not entry.strip() for entry in value):
            _log.warning("json schema invalid for %s[%s].%s: expected list of non-empty strings", filename, index, field)
            return False
        return True

    def _validate_image_field(self, filename: str, index: int, item: dict, field: str) -> bool:
        image_path = item.get(field)
        if not image_path:
            return True
        if os.path.isabs(image_path) or ".." in image_path.replace("\\", "/").split("/"):
            _log.warning("json schema invalid for %s[%s].%s: unsafe asset path", filename, index, field)
            return False
        asset_root = os.path.dirname(self._data_dir())
        normalized = image_path.replace("\\", "/")
        if normalized.startswith("image/"):
            full_path = os.path.join(asset_root, *normalized.split("/"))
        else:
            full_path = os.path.join(asset_root, "image", *normalized.split("/"))
        if not os.path.exists(full_path):
            _log.warning("json schema invalid for %s[%s].%s: missing asset %s", filename, index, field, image_path)
            return False
        return True

    def validate_static_json(self, filename: str, data: object) -> bool:
        basename = os.path.basename(filename)
        required_fields = self.REQUIRED_FIELDS.get(basename)
        if not required_fields:
            return True
        items = self._iter_items(filename, data)
        if items is None:
            _log.warning("json schema invalid for %s: expected list, got %s", filename, type(data).__name__)
            return False

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                _log.warning("json schema invalid for %s[%s]: expected object", filename, index)
                return False
            missing = [
                field for field in required_fields
                if field not in item or item[field] is None or item[field] == ""
            ]
            if missing:
                _log.warning("json schema invalid for %s[%s]: missing %s", filename, index, ", ".join(missing))
                return False
            for field in required_fields:
                if not self._validate_text_field(filename, index, item, field, required=True):
                    return False
            for field in self.OPTIONAL_TEXT_FIELDS.get(basename, ()):
                if not self._validate_text_field(filename, index, item, field, required=False):
                    return False
            for field in self.OPTIONAL_LIST_FIELDS.get(basename, ()):
                if not self._validate_list_field(filename, index, item, field):
                    return False
            for field, allowed in self.ALLOWED_VALUES.get(basename, {}).items():
                if not self._validate_allowed_value(filename, index, item, field, allowed):
                    return False
            for field in self.IMAGE_FIELDS.get(basename, ()):
                if not self._validate_image_field(filename, index, item, field):
                    return False
        return True

    def load_json(self, filename: str):
        basename = os.path.basename(filename)
        if basename not in self.REQUIRED_FIELDS:
            _log.warning("load_json: '%s' non è nella allowlist dei file consentiti", filename)
            return None
        path = os.path.join(self._data_dir(), basename)
        if not os.path.exists(path):
            return None
        try:
            mtime_ns = os.stat(path).st_mtime_ns
            with self._lock:
                cached = self._cache.get(path)
                if cached and cached[0] == mtime_ns:
                    return cached[1]
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not self.validate_static_json(filename, data):
                with self._lock:
                    self._cache.pop(path, None)
                return None
            with self._lock:
                self._cache[path] = (mtime_ns, data)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            _log.warning("json load failed for %s: %s", path, exc)
            with self._lock:
                self._cache.pop(path, None)
            return None

    def clear_cache(self, filename: str | None = None) -> None:
        with self._lock:
            if filename is None:
                self._cache.clear()
                return
            path = os.path.join(self._data_dir(), filename)
            self._cache.pop(path, None)
