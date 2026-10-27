"""Tests use injected dependencies and fictional values, never a live API."""
from types import SimpleNamespace
import pytest
from src.agents.base import Runtime
from src.config import Settings

class NoTools:
    def call(self, *args, **kwargs):
        raise AssertionError('Document and assembly agents must not calculate tax')

@pytest.fixture
def runtime(tmp_path):
    return Runtime(llm=SimpleNamespace(mode='offline'), tools=NoTools(),
                   settings=Settings(llm_mode='offline', var_dir=tmp_path / 'var'),
                   now=lambda: '2026-10-24T19:00:00+00:00')
