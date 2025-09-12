import os
import importlib


def test_translations_available():
    from bubble.i18n import load_translations, available_languages

    load_translations()
    langs = available_languages()
    # Core languages should be available
    for code in ("en", "zh", "ja", "ko", "fr"):
        assert code in langs


def test_t_fallback_to_en_and_missing_key(tmp_path, monkeypatch):
    # Force an unsupported language to trigger fallback
    from bubble import i18n

    i18n.set_language("xx")
    # Known key should fallback to English
    assert i18n.t("menu.settings").startswith("Settings")
    # Missing key should return the key itself
    assert i18n.t("__missing.key.example__") == "__missing.key.example__"


def test_env_override_language(monkeypatch):
    monkeypatch.setenv("BUBBLE_LANG", "fr")
    # Reload module to apply env override path in t()
    from bubble import i18n
    importlib.reload(i18n)
    # Known French translation
    assert i18n.t("menu.settings").startswith("Réglages")
    # Cleanup
    monkeypatch.delenv("BUBBLE_LANG", raising=False)
