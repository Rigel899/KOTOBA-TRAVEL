"""
core/content_store.py
Caricamento e validazione dei JSON statici dell'app.
"""
from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable


_log = logging.getLogger("kotoba.content")


class ContentStore:
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

    def __init__(
        self,
        data_dir: Callable[[], str],
        cache: dict[str, tuple[int, object]] | None = None,
    ) -> None:
        self._data_dir = data_dir
        self._cache = cache if cache is not None else {}

    def validate_static_json(self, filename: str, data: object) -> bool:
        required_fields = self.REQUIRED_FIELDS.get(os.path.basename(filename))
        if not required_fields:
            return True
        if not isinstance(data, list):
            _log.warning("json schema invalid for %s: expected list, got %s", filename, type(data).__name__)
            return False

        for index, item in enumerate(data):
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
        return True

    def load_json(self, filename: str):
        path = os.path.join(self._data_dir(), filename)
        if not os.path.exists(path):
            return None
        try:
            mtime_ns = os.stat(path).st_mtime_ns
            cached = self._cache.get(path)
            if cached and cached[0] == mtime_ns:
                return cached[1]
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not self.validate_static_json(filename, data):
                self._cache.pop(path, None)
                return None
            self._cache[path] = (mtime_ns, data)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            _log.warning("json load failed for %s: %s", path, exc)
            self._cache.pop(path, None)
            return None

    def clear_cache(self, filename: str | None = None) -> None:
        if filename is None:
            self._cache.clear()
            return
        path = os.path.join(self._data_dir(), filename)
        self._cache.pop(path, None)
