"""Context-window benchmark harness (§4.5) with a fake Anthropic client.

No network, no key, no OCR. The fake answers every extraction with a fixed,
valid record and reports input tokens proportional to the request (1,500 per
image plus text size), so this checks the harness, both context strategies and
the report. It is NOT a token measurement; the real numbers come from
``python run.py benchmark --all`` with an API key.
"""

import importlib.util
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]

ANSWERS = {"W-2": ("1", "18200.00"), "1099-INT": ("1", "410.25"), "1099-DIV": ("1a", "1325.00"),
           "1099-R": ("1", "6000.00"), "SSA-1099": ("5", "19800.00")}


def _load_benchmark():
    spec = importlib.util.spec_from_file_location("context_benchmark", ROOT / "scripts" / "context_benchmark.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeMessages:
    def __init__(self, log):
        self.log = log

    def create(self, **kw):
        self.log.append(kw)
        msgs = kw["messages"]
        images = sum(1 for m in msgs if isinstance(m["content"], list)
                     for b in m["content"] if isinstance(b, dict) and b.get("type") == "image")
        text = sum(len(b.get("text", "")) for m in msgs if isinstance(m["content"], list)
                   for b in m["content"] if isinstance(b, dict)) + sum(
            len(m["content"]) for m in msgs if isinstance(m["content"], str))
        form = re.search(r"Form (\S+) for", msgs[-1]["content"][-1]["text"]).group(1)
        box, amount = ANSWERS[form]
        data = {"form_type_seen": form, "tax_year": "2025", "recipient_name": "RUTH ALVAREZ",
                "recipient_ssn": "900-77-1010", "payer_name": "Fixture Payer",
                "fields": [{"box": box, "text": amount, "readable": True}], "checkboxes": [],
                "distribution_code": "7" if form == "1099-R" else None, "notes": ""}
        usage = SimpleNamespace(input_tokens=images * 1500 + text // 4, output_tokens=120,
                                cache_creation_input_tokens=0, cache_read_input_tokens=0)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=json.dumps(data))], usage=usage,
                               stop_reason="end_turn", model=kw["model"])


@pytest.fixture
def bench(tmp_path, monkeypatch):
    import src.llm

    module = _load_benchmark()
    monkeypatch.setattr(module, "TRACES", tmp_path / "traces")
    monkeypatch.setattr(module, "DOCS", tmp_path / "docs")
    (tmp_path / "docs").mkdir()
    log = []
    client = SimpleNamespace(messages=FakeMessages(log))
    client.beta = SimpleNamespace(messages=client.messages)
    real = src.llm.AnthropicLLM
    monkeypatch.setattr(src.llm, "AnthropicLLM", lambda model, effort, fallbacks: real(model, effort, fallbacks,
                                                                                        client=client))
    monkeypatch.setenv("SILVERFILE_LLM_MODE", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-tests")
    monkeypatch.setenv("ANTHROPIC_MODEL", "fake-model-for-tests")
    return SimpleNamespace(module=module, log=log, dir=tmp_path)


def test_run_all_writes_measured_report(bench):
    bench.module.run_all(proxy=False)

    assert len(bench.log) == 20
    off = json.loads((bench.dir / "traces" / "benchmark_strategy_off.json").read_text())["rows"]
    on = json.loads((bench.dir / "traces" / "benchmark_strategy_on.json").read_text())["rows"]
    off_tokens = [r["total_prompt_tokens"] for r in off]
    on_tokens = [r["total_prompt_tokens"] for r in on]
    assert all(a < b for a, b in zip(off_tokens, off_tokens[1:]))  # full thread grows every call
    assert [r["messages_sent"] for r in off] == list(range(1, 20, 2))
    assert all(r["messages_sent"] == 1 for r in on)
    assert max(on_tokens) < 2 * min(on_tokens)  # selective recall stays roughly flat
    assert sum(on_tokens) < sum(off_tokens)

    md = (bench.dir / "docs" / "metrics.md").read_text()
    assert "## Measured input tokens per document" in md
    assert "NOT YET RUN" not in md
    assert "`fake-model-for-tests`" in md
    assert "Result consistency: 10/10" in md
    assert (bench.dir / "docs" / "metrics_chart.png").stat().st_size > 0


def test_run_all_stops_before_any_call_without_key(bench, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY"):
        bench.module.run_all(proxy=False)
    assert bench.log == []
    assert not (bench.dir / "traces").exists()


def test_run_all_stops_before_any_call_without_model(bench, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL")

    with pytest.raises(SystemExit, match="ANTHROPIC_MODEL"):
        bench.module.run_all(proxy=False)
    assert bench.log == []
