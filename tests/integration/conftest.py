import os
import pytest

def pytest_collection_modifyitems(items):
    if os.environ.get('SILVERFILE_ENABLE_NATIVE_OCR')=='1': return
    for item in items:
        if 'integration' in item.path.parts:
            item.add_marker(pytest.mark.skip(reason='Image integration tests require separately verified, network-isolated native OCR'))
