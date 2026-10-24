"""Shared pytest fixtures.

Layers (docs/ACCEPTANCE_RESULTS.md):
* unit         - pure functions; agents with an in-process tool stub
* integration  - the real graph + the real MCP server over stdio + offline LLM
* live         - real Anthropic API calls (skipped unless ANTHROPIC_API_KEY is set)
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SILVERFILE_LLM_MODE", "offline")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "needs_ocr: reads document images with the native OCR engine; skipped unless "
                   "SILVERFILE_ENABLE_NATIVE_OCR=1 (see tests/integration/conftest.py)")


class LocalTools:
    """Unit-test stand-in for the MCP client: calls the same pure functions
    in-process. Integration tests use the real MCP server instead."""

    tool_names: list[str] = []

    def start(self):
        return None

    def call(self, name: str, args: dict) -> dict:
        from src.tools import tax_calculations as tc

        res = getattr(tc, name)(**args)
        res["call_id"] = f"local-{uuid.uuid4().hex[:8]}"
        res["transport"] = "in-process (unit test)"
        return res


@pytest.fixture
def local_tools():
    return LocalTools()


@pytest.fixture
def settings(tmp_path):
    from src.config import get_settings

    s = get_settings()
    s.var_dir = tmp_path / "var"
    s.llm_mode = "offline"
    s.fault_injection = ""
    return s


@pytest.fixture
def runtime(settings, local_tools):
    from src.agents.base import Runtime
    from src.llm import OfflineLLM

    return Runtime(llm=OfflineLLM(), tools=local_tools, settings=settings)


@pytest.fixture(scope="session")
def mcp_tools():
    from src.tools.mcp_client import TaxToolClient

    client = TaxToolClient()
    client.start()
    yield client
    client.close()


@pytest.fixture
def service_factory(tmp_path, mcp_tools):
    """Build services sharing one var dir (to simulate restarts) and the real MCP server."""
    from src.config import get_settings
    from src.llm import OfflineLLM
    from src.service import SilverFileService

    def make(fault: str = "", overrides: dict | None = None, var_dir: Path | None = None):
        s = get_settings()
        s.var_dir = var_dir or (tmp_path / "var")
        s.llm_mode = "offline"
        s.fault_injection = fault
        return SilverFileService(settings=s, llm=OfflineLLM(), tools=mcp_tools, overrides=overrides)

    return make


def synthetic_extraction(doc_type: str, data: dict):
    """A transcription built from a fixture's ground-truth box values.

    Test-only stand-in for the image reader: it lets graph, aggregation and
    audit behavior be tested without OCR or a model. It says nothing about how
    accurately a real image is read.
    """
    from data.generate_fixtures import _money
    from src.contracts import DocumentExtraction, ExtractedField

    boxes = {
        "W-2": {"1": data.get("box1"), "2": data.get("box2"), "3": data.get("box3", data.get("box1")),
                "5": data.get("box5", data.get("box1"))},
        "1099-INT": {b: data.get(f"box{b}") for b in ["1", "3", "4", "8"]},
        "1099-DIV": {b: data.get(f"box{b}") for b in ["1a", "1b", "2a", "4", "12"]},
        "1099-R": {b: data.get(f"box{b}") for b in ["1", "2a", "4"]},
        "SSA-1099": {"3": data.get("box3"), "4": data.get("box4", "0"), "5": data.get("box5"),
                     "6": data.get("box6", "0")},
    }[doc_type]
    checks = []
    if data.get("ira"):
        checks.append("IRA/SEP/SIMPLE")
    if data.get("box2b"):
        checks.append("Taxable amount not determined")
    if data.get("retirement_plan"):
        checks.append("Retirement plan")
    name = data.get("name") or f"{data.get('first', '')} {data.get('last', '')}".strip()
    return DocumentExtraction(
        form_type_seen=doc_type, tax_year="2025", recipient_name=name or None, recipient_ssn=data.get("ssn"),
        payer_name=data.get("employer") or data.get("payer"),
        fields=[ExtractedField(box=b, text=_money(v) or None, readable=True) for b, v in boxes.items() if v is not None],
        checkboxes=checks, distribution_code=data.get("code") if doc_type == "1099-R" else None,
        notes="synthetic test extraction")


@pytest.fixture
def synthetic_documents(monkeypatch):
    """Replace image transcription with fixture ground truth (keyed by uploaded file name)."""
    from data.generate_fixtures import CASES
    from src.agents import document_extraction

    truth: dict[str, tuple[str, dict]] = {}
    for spec in CASES.values():
        for d in spec["documents"]:
            assert d["file"] not in truth, f"fixture file name {d['file']} is not unique"
            truth[d["file"]] = (d["type"], d["data"])
    real = document_extraction.transcribe
    seen: list[str] = []

    def fake(doc, rt, metrics):
        if doc.get("source") == "manual":
            return real(doc, rt, metrics)
        doc_type, data = truth[doc["file_name"]]
        seen.append(doc["file_name"])
        return synthetic_extraction(doc_type, data)

    monkeypatch.setattr(document_extraction, "transcribe", fake)
    return seen
