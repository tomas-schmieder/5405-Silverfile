"""Anthropic mode needs an API key; the model defaults to DEFAULT_ANTHROPIC_MODEL unless ANTHROPIC_MODEL is set."""

import pytest

from src.config import DEFAULT_ANTHROPIC_MODEL, Settings, get_settings
from src.llm import AnthropicLLM, ModelConfigError, OfflineLLM, build_llm


@pytest.mark.parametrize("value", [None, "", "   "])
def test_unset_model_uses_the_default(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    else:
        monkeypatch.setenv("ANTHROPIC_MODEL", value)
    assert DEFAULT_ANTHROPIC_MODEL
    assert Settings().anthropic_model == DEFAULT_ANTHROPIC_MODEL
    assert get_settings().anthropic_model == DEFAULT_ANTHROPIC_MODEL


def test_configured_model_overrides_the_default(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "configured-model")
    assert get_settings().anthropic_model == "configured-model"


@pytest.mark.parametrize("model", [None, "configured-model"])
def test_anthropic_mode_without_key_is_a_clear_error(monkeypatch, model):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    if model is None:
        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    else:
        monkeypatch.setenv("ANTHROPIC_MODEL", model)
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "anthropic")
    with pytest.raises(ModelConfigError) as exc:
        build_llm(get_settings())
    assert "ANTHROPIC_API_KEY" in str(exc.value)
    assert "ANTHROPIC_MODEL" not in str(exc.value)


def test_key_without_model_builds_the_live_client_with_the_default(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "anthropic")
    llm = build_llm(get_settings())
    assert isinstance(llm, AnthropicLLM) and llm.model == DEFAULT_ANTHROPIC_MODEL


def test_configured_anthropic_mode_builds_the_live_client_without_calling_it(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setenv("ANTHROPIC_MODEL", "configured-model")
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "anthropic")
    llm = build_llm(get_settings())
    assert isinstance(llm, AnthropicLLM) and llm.model == "configured-model"


def test_auto_mode_without_key_is_offline(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "auto")
    assert isinstance(build_llm(get_settings()), OfflineLLM)


def test_offline_mode_needs_no_model(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "offline")
    assert isinstance(build_llm(get_settings()), OfflineLLM)
