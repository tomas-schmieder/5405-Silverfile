import json
from pathlib import Path
import pymupdf
import pytest
from pypdf import PdfReader
from src.agents.return_assembly import assembly_node
from src.output.pdf_fields import F1040SR_TEXT, F1040SR_CHECKBOX, SCH1A_TEXT
from src.output.pdf_writer import build_field_values, write_draft, verify_pdf, render_previews
from src.provenance import MONEY_LINES_REQUIRED

def ready_state():
    lines = {k: {'value': '0', 'facts_version': 1} for k in MONEY_LINES_REQUIRED}
    prov = {f'line:{k}': {'kind': 'derived', 'value': '0', 'inputs': {}} for k in lines}
    return {'case_id': 'synthetic', 'facts_version': 1,
            'facts': {'tp.first_name': {'value': 'Fictional', 'status': 'confirmed'},
                      'tp.last_name': {'value': 'Sample', 'status': 'confirmed'},
                      'tp.ssn': {'value': '900-11-2222', 'status': 'confirmed'},
                      'filing_status': {'value': 'single', 'status': 'confirmed'}},
            'lines': lines, 'provenance': prov, 'calc': {'calc_id': 'synthetic-calc'},
            'review': {'status': 'passed', 'passed_for': {'facts_version': 1, 'calc': 'synthetic-calc'}}}

def test_assembly_blocks_without_current_audit(runtime):
    state = ready_state()
    state['review']['passed_for']['calc'] = 'old'
    out = assembly_node(state, runtime)
    assert out['assembly']['status'] == 'awaiting_audit'
    assert not runtime.settings.outputs_dir.exists()

def test_assembly_blocks_stale_line(runtime):
    state = ready_state()
    state['lines']['16']['facts_version'] = 0
    out = assembly_node(state, runtime)
    assert out['assembly']['status'] == 'gaps' and out['assembly']['stale'] == ['16']

def test_assembly_blocks_missing_provenance(runtime):
    state = ready_state()
    del state['provenance']['line:16']
    out = assembly_node(state, runtime)
    assert out['assembly']['status'] == 'gaps'
    assert not runtime.settings.outputs_dir.exists()

def test_assembly_produces_draft_previews_and_audit(runtime):
    out = assembly_node(ready_state(), runtime)
    a = out['assembly']
    assert a['status'] == 'ready', a
    assert Path(a['pdf_path']).is_file() and len(a['previews']) == 4
    audit = json.loads(Path(a['audit_path']).read_text())
    assert audit['status'] == 'DRAFT - not filed'
    assert audit['lines']['16']['value'] == '0'
    assert a['pdf_check']['logical_ok'] and a['pdf_check']['visible_ok']

@pytest.mark.parametrize('status', ['single', 'mfj', 'mfs', 'hoh', 'qss'])
def test_filing_status_checkbox_is_verified(status, tmp_path):
    values = build_field_values({'filing_status': status, 'tp.ssn': '900-11-2222'},
                               {'16': {'value': '1234'}}, {}, {}, None)
    result = write_draft(values, tmp_path / f'{status}.pdf')
    assert result['logical_ok'], result
    assert result['visible_ok'], result
    assert any('c1_8' in k and v == 'checked' for k, v in result['written'].items())

def test_schedule_appended_with_interactive_fields(tmp_path):
    values = build_field_values({'filing_status': 'single', 'tp.first_name': 'Fictional',
                                 'tp.last_name': 'Sample', 'tp.ssn': '900-11-2222'},
                                {'13b': {'value': '6000'}}, {'tp_65': True},
                                {'sch1a_31': '10000', 'sch1a_36a': '6000', 'sch1a_38': '6000'}, '1')
    path = tmp_path / 'schedule.pdf'
    result = write_draft(values, path)
    assert result['pages'] == 6
    assert result['logical_ok'] and result['visible_ok'], result
    reader = PdfReader(path)
    assert reader.get_fields()
    assert any(str(f.get('/V')) == '6,000' for f in reader.get_fields().values())

def test_unknown_requested_field_is_not_silently_ignored(tmp_path):
    with pytest.raises(ValueError, match='missing requested fields'):
        write_draft({'text': {'nonexistent': '500'}, 'checks': [], 'filing_status': 'single'},
                    tmp_path / 'bad.pdf')

def test_checkbox_tampering_is_detected(tmp_path):
    path = tmp_path / 'before.pdf'
    result = write_draft(build_field_values({'filing_status': 'single'}, {}, {'tp_65': True}, {}, '1'), path)
    doc = pymupdf.open(path)
    for w in doc[1].widgets():
        if w.field_name.split('.')[-1] == F1040SR_CHECKBOX['12d_tp_born_before']:
            w.field_value = 'Off'
            w.update()
    changed = tmp_path / 'changed.pdf'
    doc.save(changed)
    doc.close()
    assert not verify_pdf(changed, result['written'])['logical_ok']

def test_product_pdf_has_no_classroom_wording(tmp_path):
    path = tmp_path / 'wording.pdf'
    write_draft(build_field_values({'filing_status': 'single'}, {}, {}, {}, None), path)
    with pymupdf.open(path) as doc:
        text = ''.join(p.get_text() for p in doc)
    assert 'classroom' not in text.lower()
    assert 'DRAFT' in text and 'FICTIONAL DATA' in text
