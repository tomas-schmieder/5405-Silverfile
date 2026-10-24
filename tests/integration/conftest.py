"""Integration tests run in the core suite, except those that read document images.

Tests marked ``needs_ocr`` pass real fixture images through the offline back end,
which uses the native OCR engine. That engine stays disabled until it has been
validated in a network-isolated environment (docs/KNOWN_LIMITATIONS.md), so those
tests are skipped unless SILVERFILE_ENABLE_NATIVE_OCR=1. Everything else here runs
the real graph and the real stdio MCP server without OCR.
"""

import os

import pytest


def pytest_collection_modifyitems(items):
    if os.environ.get("SILVERFILE_ENABLE_NATIVE_OCR") == "1":
        return
    skip = pytest.mark.skip(reason="reads document images with native OCR, which needs separately verified, "
                                   "network-isolated execution")
    for item in items:
        if item.get_closest_marker("needs_ocr"):
            item.add_marker(skip)
