"""Local fixtures: never call a model or calculation service."""
from types import SimpleNamespace
import pytest
from src.agents.base import Runtime
from src.config import Settings

class NoTools:
    def call(self, *args, **kwargs):
        raise AssertionError("Intake tests must not perform tax calculations")

@pytest.fixture
def runtime(tmp_path):
    return Runtime(llm=SimpleNamespace(mode="offline"), tools=NoTools(),
                   settings=Settings(llm_mode="offline", var_dir=tmp_path/"var"),
                   now=lambda: "2026-10-24T12:00:00+00:00")
