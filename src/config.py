"""Runtime configuration for SilverFile.

All settings come from environment variables (optionally loaded from a local,
git-ignored ``.env`` file). Nothing secret is ever hard-coded here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv is optional at import time so unit tests stay light
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FORMS_DIR = DATA_DIR / "reference_tax_forms" / "forms"
REFERENCE_DIR = DATA_DIR / "reference_tax_forms" / "reference"

TAX_YEAR = 2025
SCHEMA_VERSION = 1

# Loop-control settings (documented project choices, see docs/IMPLEMENTATION_NOTES.md)
MAX_REVIEW_PASSES = 3
MAX_HANDOFFS_PER_RUN = 30
MAX_SIGNATURE_REPEATS = 4

# Vision + structured-output model used when ANTHROPIC_MODEL is not set
DEFAULT_ANTHROPIC_MODEL = "claude-opus-5-5"


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def native_ocr_enabled() -> bool:
    """Offline document reading with RapidOCR on ONNX Runtime.

    On by default: the OCR models ship inside the package and the reader makes
    no network calls (verified with outbound networking denied, see
    docs/ACCEPTANCE_RESULTS.md). Set SILVERFILE_ENABLE_NATIVE_OCR=0 to turn it off.
    """
    return _bool("SILVERFILE_ENABLE_NATIVE_OCR", True)


@dataclass
class Settings:
    """Resolved settings. Construct with :func:`get_settings`."""

    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL  # override with ANTHROPIC_MODEL
    llm_mode: str = "auto"  # auto | anthropic | offline
    effort: str = "low"
    use_fallbacks: bool = True
    var_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "var")
    context_strategy: bool = True
    context_recent_turns: int = 4
    fault_injection: str = ""  # test/demo only, e.g. "line16_once"

    @property
    def db_path(self) -> Path:
        return self.var_dir / "silverfile.db"

    @property
    def checkpoint_path(self) -> Path:
        return self.var_dir / "checkpoints.db"

    @property
    def uploads_dir(self) -> Path:
        return self.var_dir / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.var_dir / "outputs"

    def resolved_llm_mode(self) -> str:
        """Return ``anthropic`` or ``offline``.

        ``auto`` uses Anthropic when an API key (or auth token) is configured,
        otherwise the deterministic offline mode documented in the README.
        """
        if self.llm_mode in {"anthropic", "offline"}:
            return self.llm_mode
        return "anthropic" if self.has_api_credentials() else "offline"

    @staticmethod
    def has_api_credentials() -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))

    def live_model_problem(self) -> str | None:
        """Why the Anthropic (vision) path cannot be used, or None when it is configured.

        Never reports credential values, only whether they are present.
        """
        missing = []
        if not self.has_api_credentials():
            missing.append("ANTHROPIC_API_KEY")
        if not self.anthropic_model:
            missing.append("ANTHROPIC_MODEL")
        if not missing:
            return None
        return (f"Model mode is 'anthropic' but {' and '.join(missing)} {'is' if len(missing) == 1 else 'are'} not set. "
                f"Set {'it' if len(missing) == 1 else 'them'} in .env, or set SILVERFILE_LLM_MODE=auto "
                "(or offline) to read documents with native "
                "OCR instead.")


def get_settings() -> Settings:
    var_dir = Path(os.environ.get("SILVERFILE_VAR_DIR", str(PROJECT_ROOT / "var")))
    return Settings(
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "").strip() or DEFAULT_ANTHROPIC_MODEL,
        llm_mode=os.environ.get("SILVERFILE_LLM_MODE", "auto").strip().lower(),
        effort=os.environ.get("SILVERFILE_EFFORT", "low").strip().lower(),
        use_fallbacks=_bool("SILVERFILE_FALLBACKS", True),
        var_dir=var_dir,
        context_strategy=_bool("SILVERFILE_CONTEXT_STRATEGY", True),
        context_recent_turns=int(os.environ.get("SILVERFILE_CONTEXT_RECENT_TURNS", "4")),
        fault_injection=os.environ.get("SILVERFILE_FAULT_INJECTION", "").strip(),
    )
