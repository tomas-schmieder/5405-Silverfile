"""Anthropic mode needs an explicitly configured model; no identifier is assumed."""

import pytest

from src.config import Settings, get_settings
from src.llm import AnthropicLLM, ModelConfigError, OfflineLLM, build_llm


def test_no_default_model_identifier(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    assert Settings().anthropic_model == ""
    assert get_settings().anthropic_model == ""


@pytest.mark.parametrize("key,model,missing", [
    (None, None, ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"]),
    ("test-key-not-real", None, ["ANTHROPIC_MODEL"]),
    (None, "configured-model", ["ANTHROPIC_API_KEY"]),
])
def test_anthropic_mode_without_key_or_model_is_a_clear_error(monkeypatch, key, model, missing):
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    for name, value in [("ANTHROPIC_API_KEY", key), ("ANTHROPIC_MODEL", model)]:
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "anthropic")
    with pytest.raises(ModelConfigError) as exc:
        build_llm(get_settings())
    for name in missing:
        assert name in str(exc.value)
    assert "test-key-not-real" not in str(exc.value)


def test_configured_anthropic_mode_builds_the_live_client_without_calling_it(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setenv("ANTHROPIC_MODEL", "configured-model")
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "anthropic")
    llm = build_llm(get_settings())
    assert isinstance(llm, AnthropicLLM) and llm.model == "configured-model"


def test_offline_mode_needs_no_model(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "offline")
    assert isinstance(build_llm(get_settings()), OfflineLLM)
