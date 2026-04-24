from __future__ import annotations

from app.core.config import Settings, get_settings


def test_openrouter_api_key_defaults_empty(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    get_settings.cache_clear()

    try:
        settings = Settings(_env_file=None)
        assert settings.openrouter_api_key == ""
    finally:
        get_settings.cache_clear()
