"""
ConfigManager: manages user configuration persistence for Bubble.

For now it uses the existing BubbleBot path; Task 0.2 will migrate paths.
Responsibilities here focus on default language detection and language get/set.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    # Optional dependency; only available on macOS with PyObjC
    from Foundation import NSLocale
except Exception:  # pragma: no cover
    NSLocale = None  # type: ignore


class ConfigManager:
    @classmethod
    def config_path(cls) -> str:
        # Will be migrated in Task 0.2
        return os.path.expanduser("~/Library/Application Support/BubbleBot/config.json")

    @classmethod
    def _ensure_dir(cls) -> None:
        d = os.path.dirname(cls.config_path())
        os.makedirs(d, exist_ok=True)

    @classmethod
    def load(cls) -> Dict[str, Any]:
        p = cls.config_path()
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    @classmethod
    def save(cls, cfg: Dict[str, Any]) -> None:
        try:
            cls._ensure_dir()
            with open(cls.config_path(), "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception as e:  # pragma: no cover
            print(f"WARNING[config]: failed to save config: {e}")

    @classmethod
    def get_language(cls) -> Optional[str]:
        cfg = cls.load()
        lang = cfg.get("language")
        if isinstance(lang, str) and lang:
            return lang
        return None

    @classmethod
    def set_language(cls, lang: str) -> None:
        cfg = cls.load()
        cfg["language"] = lang
        cls.save(cfg)

    @classmethod
    def detect_system_language(cls) -> str:
        # Preferred: macOS NSLocale preferredLanguages (e.g. zh-Hans-CN)
        code: Optional[str] = None
        try:
            if NSLocale is not None:
                arr = NSLocale.preferredLanguages()
                if arr and len(arr) > 0:
                    code = str(arr[0])
        except Exception:
            code = None
        # Fallbacks: environment LANG or locale module
        if not code:
            code = os.environ.get("LANG", "en")
        code = code.lower().replace("_", "-")
        # Normalize to supported set
        if code.startswith("zh"):
            return "zh"
        if code.startswith("ja"):
            return "ja"
        if code.startswith("ko"):
            return "ko"
        if code.startswith("fr"):
            return "fr"
        return "en"

