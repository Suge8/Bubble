"""
ConfigManager: manages user configuration persistence for Bubble.

Uses the new Bubble path; retains migration support from BubbleBot.
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
    _FILENAME = "config.json"

    @classmethod
    def _new_app_support_dir(cls) -> str:
        return os.path.expanduser("~/Library/Application Support/Bubble")

    @classmethod
    def _old_app_support_dir(cls) -> str:
        return os.path.expanduser("~/Library/Application Support/BubbleBot")

    @classmethod
    def config_path(cls) -> str:
        # New location after Task 0.2 migration
        return os.path.join(cls._new_app_support_dir(), cls._FILENAME)

    @classmethod
    def legacy_config_path(cls) -> str:
        # Legacy (pre-rename) location
        return os.path.join(cls._old_app_support_dir(), cls._FILENAME)

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
            # Fallback read from legacy path (no writeback here; migration handles that)
            lp = cls.legacy_config_path()
            if os.path.exists(lp):
                with open(lp, "r", encoding="utf-8") as f:
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

    # ----- Suspend (sleep) minutes -----
    @classmethod
    def get_suspend_minutes(cls, default: int = 30) -> int:
        """Return configured suspend minutes; 0 means disabled.

        If key missing or invalid, return default (30).
        """
        try:
            cfg = cls.load()
            val = cfg.get("suspend", {}).get("minutes", default)
            minutes = int(val)
            # 0 or greater allowed; negative treated as default
            return minutes if minutes >= 0 else default
        except Exception:
            return default

    @classmethod
    def set_suspend_minutes(cls, minutes: int) -> None:
        cfg = cls.load()
        suspend = cfg.get("suspend") if isinstance(cfg.get("suspend"), dict) else {}
        try:
            suspend["minutes"] = int(minutes)
        except Exception:
            suspend["minutes"] = minutes
        cfg["suspend"] = suspend
        cls.save(cfg)

    # ----- Navigation allow hosts -----
    @classmethod
    def get_allowed_hosts(cls) -> list:
        try:
            cfg = cls.load()
            val = cfg.get("navigation", {}).get("allow_hosts", [])
            return list(val) if isinstance(val, (list, tuple)) else []
        except Exception:
            return []

    @classmethod
    def set_allowed_hosts(cls, hosts: list[str]) -> None:
        cfg = cls.load()
        nav = cfg.get("navigation") if isinstance(cfg.get("navigation"), dict) else {}
        nav["allow_hosts"] = list(hosts or [])
        cfg["navigation"] = nav
        cls.save(cfg)

    # ----- Hotkeys: switcher (cycle window) -----
    @classmethod
    def get_switcher_hotkey(cls) -> dict:
        try:
            cfg = cls.load()
            hk = cfg.get("hotkeys", {}).get("switcher", {})
            if isinstance(hk, dict) and "flags" in hk and "key" in hk:
                return {"flags": hk["flags"], "key": hk["key"]}
        except Exception:
            pass
        return {}

    @classmethod
    def set_switcher_hotkey(cls, flags: int, key: int) -> None:
        cfg = cls.load()
        hot = cfg.get("hotkeys") if isinstance(cfg.get("hotkeys"), dict) else {}
        hot["switcher"] = {"flags": int(flags), "key": int(key)}
        cfg["hotkeys"] = hot
        cls.save(cfg)

    @classmethod
    def migrate_config_if_needed(cls) -> bool:
        """Migrate config from BubbleBot -> Bubble, keeping a backup and flagging a one-time notice.

        Returns True if a migration was performed.
        """
        try:
            new_p = cls.config_path()
            old_p = cls.legacy_config_path()
            # Ensure new dir exists
            os.makedirs(os.path.dirname(new_p), exist_ok=True)
            if os.path.exists(new_p):
                return False  # already migrated/created
            if not os.path.exists(old_p):
                return False  # nothing to migrate

            # Copy old -> new
            try:
                with open(old_p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

            # Stamp migration meta and set notice flag
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
            meta.update({
                "migrated_from": "BubbleBot",
                "migration_notice_pending": True,
                "legacy_path": old_p,
            })
            data["meta"] = meta

            # Save to new path
            with open(new_p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Also create a timestamped backup alongside the new file and keep ≤5
            try:
                import datetime
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                backup_p = os.path.join(os.path.dirname(new_p), f"config.backup.{ts}.json")
                with open(backup_p, "w", encoding="utf-8") as bf:
                    json.dump(data, bf, indent=2, ensure_ascii=False)
                # prune old backups beyond 5
                prefix = os.path.join(os.path.dirname(new_p), "config.backup.")
                backups = [p for p in os.listdir(os.path.dirname(new_p)) if p.startswith("config.backup.") and p.endswith('.json')]
                backups.sort(reverse=True)
                for old in backups[5:]:
                    try:
                        os.remove(os.path.join(os.path.dirname(new_p), old))
                    except Exception:
                        pass
            except Exception:
                pass
            return True
        except Exception as e:
            print(f"WARNING[config]: migration failed: {e}")
            return False

    @classmethod
    def needs_migration_notice(cls) -> bool:
        try:
            cfg = cls.load()
            meta = cfg.get("meta") if isinstance(cfg.get("meta"), dict) else {}
            return bool(meta.get("migration_notice_pending", False))
        except Exception:
            return False

    @classmethod
    def mark_migration_notice_shown(cls) -> None:
        try:
            cfg = cls.load()
            meta = cfg.get("meta") if isinstance(cfg.get("meta"), dict) else {}
            meta["migration_notice_pending"] = False
            meta["migration_notice_shown"] = True
            cfg["meta"] = meta
            cls.save(cfg)
        except Exception:
            pass

    # ----- First-run flags: onboarding / permissions -----
    @classmethod
    def is_onboarding_shown(cls) -> bool:
        try:
            cfg = cls.load()
            meta = cfg.get("meta") if isinstance(cfg.get("meta"), dict) else {}
            return bool(meta.get("onboarding_shown", False))
        except Exception:
            return False

    @classmethod
    def mark_onboarding_shown(cls) -> None:
        try:
            cfg = cls.load()
            meta = cfg.get("meta") if isinstance(cfg.get("meta"), dict) else {}
            meta["onboarding_shown"] = True
            cfg["meta"] = meta
            cls.save(cfg)
        except Exception:
            pass

    @classmethod
    def is_permissions_prompted(cls) -> bool:
        try:
            cfg = cls.load()
            meta = cfg.get("meta") if isinstance(cfg.get("meta"), dict) else {}
            return bool(meta.get("permissions_prompted", False))
        except Exception:
            return False

    @classmethod
    def mark_permissions_prompted(cls) -> None:
        try:
            cfg = cls.load()
            meta = cfg.get("meta") if isinstance(cfg.get("meta"), dict) else {}
            meta["permissions_prompted"] = True
            cfg["meta"] = meta
            cls.save(cfg)
        except Exception:
            pass

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
