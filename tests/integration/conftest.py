"""Integration tests through the real graph and the real stdio MCP server.

Tests marked ``needs_ocr`` pass real fixture images through the offline back end,
which uses the native OCR engine. Native OCR is on by default; with
SILVERFILE_ENABLE_NATIVE_OCR=0 those tests are skipped and everything else here
still runs.
"""

import pytest

from src.config import native_ocr_enabled


def pytest_collection_modifyitems(items):
    if native_ocr_enabled():
        return
    skip = pytest.mark.skip(reason="reads document images with native OCR, which is turned off "
                                   "(SILVERFILE_ENABLE_NATIVE_OCR=0)")
    for item in items:
        if item.get_closest_marker("needs_ocr"):
            item.add_marker(skip)
