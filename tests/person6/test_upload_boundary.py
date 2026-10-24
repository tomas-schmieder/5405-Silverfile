import pytest
import pymupdf
from src.service import _normalise_image, ServiceError

def test_multpage_pdf_is_not_silently_truncated():
    with pymupdf.open() as doc:
        doc.new_page(); doc.new_page(); data=doc.tobytes()
    with pytest.raises(ServiceError,match='one PDF page'):
        _normalise_image(data)

def test_single_page_pdf_is_normalized():
    with pymupdf.open() as doc:
        doc.new_page(); data=doc.tobytes()
    data, media=_normalise_image(data)
    assert data.startswith(b'\x89PNG') and media=='image/png'
