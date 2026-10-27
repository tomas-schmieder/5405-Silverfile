"""Native OCR accuracy on the fixture images. Skipped when SILVERFILE_ENABLE_NATIVE_OCR=0."""
import pytest

from src.config import native_ocr_enabled

def pytest_collection_modifyitems(items):
    if native_ocr_enabled():
        return
    skip = pytest.mark.skip(reason='Native OCR is turned off (SILVERFILE_ENABLE_NATIVE_OCR=0)')
    for item in items:
        if 'native_ocr' in item.path.parts:
            item.add_marker(skip)
