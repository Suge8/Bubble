import json
import os
from typing import Any, Dict, Optional
import pkgutil

_CURRENT_LANG = "en"
_TRANSLATIONS: Dict[str, Dict[str, Any]] = {}
_BASE_DIR = os.path.dirname(__file__)

_LANG_ALIASES = {
    "zh": "zh",
    "zh-cn": "zh",
    "zh_cn": "zh",
    "zh-hans": "zh",
    "en": "en",
    "en-us": "en",
    "en_gb": "en",
    "ja": "ja",
    "ja-jp": "ja",
    "ko": "ko",
    "ko-kr": "ko",
    "fr": "fr",
    "fr-fr": "fr",
}


def _normalize_lang(code: Optional[str]) -> str:
    if not code:
        return "en"
    c = code.strip().lower()
    return _LANG_ALIASES.get(c, c.split("-")[0].split("_")[0])


def _load_lang(code: str) -> Dict[str, Any]:
    """Load translations for a language.

    Zip-safe: first try pkgutil.get_data (works in py2app bundles where files
    are inside python313.zip). Fallback to file path during dev runs.
    """
    # 1) Zip-safe import from package data
    try:
        data = pkgutil.get_data(__package__ or 'bubble.i18n', f"strings_{code}.json")
        if data:
            return json.loads(data.decode("utf-8"))
    except Exception:
        pass

    # 2) File path fallback (source tree / editable installs)
    path = os.path.join(_BASE_DIR, f"strings_{code}.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"WARNING[i18n]: Failed to load language '{code}': {e}")
    return {}


def load_translations() -> None:
    global _TRANSLATIONS
    _TRANSLATIONS = {}
    for code in ("en", "zh", "ja", "ko", "fr"):
        _TRANSLATIONS[code] = _load_lang(code)


def available_languages():
    return [k for k in sorted(_TRANSLATIONS.keys())]


def set_language(code: Optional[str]) -> None:
    global _CURRENT_LANG
    norm = _normalize_lang(code)
    if norm not in _TRANSLATIONS:
        # try lazy-load
        _TRANSLATIONS[norm] = _load_lang(norm)
    _CURRENT_LANG = norm if norm in _TRANSLATIONS else "en"


def get_language() -> str:
    return _CURRENT_LANG


def _get_value(d: Dict[str, Any], key: str) -> Optional[str]:
    # direct key first
    if key in d:
        v = d[key]
        return v if isinstance(v, str) else None
    # dot-path drill-down
    cur: Any = d
    for part in key.split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur if isinstance(cur, str) else None


def t(key: str, **kwargs) -> str:
    """Translate a key to the current language; fallback to English.

    Examples:
        t('menu.showHideHint', hotkey='⌘+G')
    """
    if not _TRANSLATIONS:
        load_translations()

    lang = get_language()
    # env override if present
    env_lang = os.environ.get("BUBBLE_LANG")
    if env_lang:
        lang = _normalize_lang(env_lang)

    # Extract optional default text without feeding it into .format(**kwargs)
    default_text = None
    try:
        if 'default' in kwargs:
            default_text = kwargs.pop('default')
    except Exception:
        default_text = None

    bundle = _TRANSLATIONS.get(lang) or {}
    en_bundle = _TRANSLATIONS.get("en") or {}

    text = _get_value(bundle, key)
    if text is None:
        text = _get_value(en_bundle, key)
        if text is None and default_text is not None:
            text = default_text
        else:
            print(f"WARNING[i18n]: Missing key '{key}' in lang '{lang}', falling back to 'en'")
    if text is None:
        print(f"WARNING[i18n]: Missing key '{key}' in 'en' and no default; returning key")
        return key
    try:
        return text.format(**kwargs) if kwargs else text
    except Exception as e:
        print(f"WARNING[i18n]: Format error for key '{key}': {e}")
        return text


# Initialize translations and current language (env override or default 'en')
try:
    load_translations()
    set_language(os.environ.get("BUBBLE_LANG", "en"))
except Exception:
    _CURRENT_LANG = "en"

__all__ = [
    "t",
    "set_language",
    "get_language",
    "available_languages",
    "load_translations",
]
