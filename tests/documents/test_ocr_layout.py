"""Layout logic with controlled OCR tokens; these do not initialize native OCR."""
from PIL import Image
import pytest
from src.tools import ocr_reader as reader

def test_native_engine_can_be_turned_off(monkeypatch):
    monkeypatch.setenv('SILVERFILE_ENABLE_NATIVE_OCR', '0')
    with pytest.raises(RuntimeError, match='turned off'):
        reader._ocr()

@pytest.mark.parametrize('value,enabled', [(None, True), ('', True), ('1', True), ('0', False), ('false', False)])
def test_native_engine_is_on_by_default(monkeypatch, value, enabled):
    from src.config import native_ocr_enabled
    if value is None:
        monkeypatch.delenv('SILVERFILE_ENABLE_NATIVE_OCR', raising=False)
    else:
        monkeypatch.setenv('SILVERFILE_ENABLE_NATIVE_OCR', value)
    assert native_ocr_enabled() is enabled

def test_value_below_does_not_borrow_neighbor_column():
    label = reader.Token(100, 10, 170, 20, '1 Wages, tips', 1)
    neighbor = reader.Token(200, 10, 280, 20, '2 Federal income tax', 1)
    wrong = reader.Token(210, 30, 270, 40, '999.00', 1)
    assert reader._value_below([label, neighbor, wrong], label, reader.MONEY_RE) is None

def test_low_confidence_amount_is_marked_unreadable(monkeypatch):
    tokens = [reader.Token(10, 0, 40, 10, 'W-2', 1),
              reader.Token(100, 10, 170, 20, '1 Wages, tips', 1),
              reader.Token(100, 25, 160, 35, '123.45', .4)]
    monkeypatch.setattr(reader, 'read_tokens', lambda b: (tokens, Image.new('RGB', (300, 100), 'white')))
    ex = reader.extract(b'synthetic', 'W-2')
    field = next(f for f in ex.fields if f.box == '1')
    assert field.text == '123.45' and not field.readable

def test_unknown_form_does_not_inherit_declared_identity(monkeypatch):
    tokens = [reader.Token(100, 10, 170, 20, '1 Wages, tips', 1)]
    monkeypatch.setattr(reader, 'read_tokens', lambda b: (tokens, Image.new('RGB', (300, 100), 'white')))
    assert reader.extract(b'synthetic', 'W-2').form_type_seen == 'other'
