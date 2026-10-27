"""Native OCR is explicitly opt-in, after network-isolated verification setup.

The current host blocked a native telemetry request even with the ONNX setting
disabled. Ordinary test runs must not silently initialize that runtime.
"""
import os
import pytest

def pytest_collection_modifyitems(items):
    if os.environ.get('SILVERFILE_ENABLE_NATIVE_OCR') == '1':
        return
    skip = pytest.mark.skip(reason='Native OCR needs an explicitly enabled, network-isolated test run')
    for item in items:
        if 'native_ocr' in item.path.parts:
            item.add_marker(skip)
