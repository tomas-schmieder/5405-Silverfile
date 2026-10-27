import copy
from types import SimpleNamespace
import pytest
from src.agents.document_extraction import build_record, aggregate_extractions_node, extract_document_node, transcribe
from src.contracts import DocumentExtraction, ExtractedField
from src.state import merge_extractions
from src.tools.document_input import image_block

def extraction(kind='W-2', **changes):
    values = dict(form_type_seen=kind, tax_year='2025', recipient_name='Fictional Person',
                  recipient_ssn='900-11-2222', payer_name='Fictional Payer',
                  fields=[ExtractedField(box='1', text='1000.25', readable=True)],
                  checkboxes=[], distribution_code='7' if kind == '1099-R' else None, notes='')
    values.update(changes)
    return DocumentExtraction(**values)

def record(doc_id='d1', kind='W-2', **changes):
    return build_record({'doc_id': doc_id, 'doc_type': kind, 'source': 'upload'},
                        extraction(kind, **changes), 'offline', None, 'now')

def state_for(*records):
    return {'facts': {'tp.ssn': {'value': '900-11-2222', 'status': 'confirmed'},
                      'filing_status': {'value': 'single', 'status': 'confirmed'}},
            'documents': {r['doc_id']: {'doc_id': r['doc_id'], 'doc_type': r['doc_type'],
                                      'source': 'upload', 'status': 'extracted'} for r in records},
            'extractions': {r['doc_id']: r for r in records}}

@pytest.mark.parametrize('text', [None, '', 'illegible', '123.00'])
def test_unreadable_optional_amount_is_not_zero(text, runtime):
    r = record(fields=[ExtractedField(box='1', text='1000.25', readable=True),
                       ExtractedField(box='2', text=text, readable=False)])
    assert r['fields']['2']['value'] is None
    assert r['fields']['2']['readable'] is False
    out = aggregate_extractions_node(state_for(r), runtime)
    assert out['documents']['d1']['status'] == 'rejected'
    assert not out['source_facts']

def test_explicit_blank_optional_box_remains_zero():
    r = record(fields=[ExtractedField(box='1', text='1000.25', readable=True),
                       ExtractedField(box='2', text=None, readable=True)])
    assert r['fields']['2']['value'] == '0.00'
    assert r['fields']['2']['blank'] and not r['issues']

@pytest.mark.parametrize('seen', ['other', 'unreadable'])
def test_unknown_form_is_rejected_even_with_plausible_amount(seen, runtime):
    r = record(form_type_seen=seen)
    out = aggregate_extractions_node(state_for(r), runtime)
    assert out['documents']['d1']['status'] == 'rejected'
    assert not out['source_facts']

def test_known_mislabelled_form_is_reclassified():
    r = record(form_type_seen='1099-INT')
    assert r['doc_type'] == '1099-INT' and not r['issues']

def test_wrong_year_not_published(runtime):
    out = aggregate_extractions_node(state_for(record(tax_year='2024')), runtime)
    assert not out['source_facts']

def test_money_cents_and_provenance_survive(runtime):
    out = aggregate_extractions_node(state_for(record()), runtime)
    assert out['source_facts']['doc:d1:1']['value'] == '1000.25'
    assert out['provenance']['doc:d1:1']['raw_text'] == '1000.25'
    assert out['provenance']['doc:d1:1']['extracted_at'] == 'now'

def test_w2_box6_is_published_with_provenance(runtime):
    r = record(fields=[ExtractedField(box='1', text='250,000.00', readable=True),
                       ExtractedField(box='5', text='250,000.00', readable=True),
                       ExtractedField(box='6', text='4,225.00', readable=True)])
    assert r['fields']['6']['label'] == 'Medicare tax withheld' and r['fields']['6']['value'] == '4225.00'
    assert not r['issues']
    out = aggregate_extractions_node(state_for(r), runtime)
    assert out['source_facts']['doc:d1:6']['value'] == '4225.00'
    assert out['source_facts']['doc:d1:5']['value'] == '250000.00'
    assert out['provenance']['doc:d1:6']['raw_text'] == '4,225.00'

def test_w2_box6_is_optional_like_box5():
    r = record()
    for box in ('5', '6'):
        assert r['fields'][box]['blank'] and r['fields'][box]['value'] == '0.00'
    assert not r['issues']

def test_unreadable_w2_box6_is_not_zero(runtime):
    r = record(fields=[ExtractedField(box='1', text='1000.25', readable=True),
                       ExtractedField(box='6', text='4,2?5.00', readable=False)])
    assert r['fields']['6']['value'] is None
    out = aggregate_extractions_node(state_for(r), runtime)
    assert out['documents']['d1']['status'] == 'rejected'
    assert not out['source_facts']

def test_identical_duplicate_is_counted_once(runtime):
    out = aggregate_extractions_node(state_for(record('a'), record('b')), runtime)
    assert out['extraction_summary']['usable_documents'] == 1
    assert out['documents']['b']['status'] == 'duplicate'

@pytest.mark.parametrize('flagged_id', ['a', 'z'])
def test_box2b_survives_duplicate_order(flagged_id, runtime):
    flagged = record(flagged_id, '1099-R', checkboxes=['Taxable amount not determined'])
    plain = record('m', '1099-R')
    out = aggregate_extractions_node(state_for(plain, flagged), runtime)
    assert out['escalation']['reason'] == 'form_1099r_2b'
    assert out['documents'][flagged_id]['status'] != 'duplicate'
    assert f'doc:{flagged_id}:1' not in out['source_facts']

def test_box2b_survives_parallel_conflict(runtime):
    a = record('d1', '1099-R')
    b = record('d1', '1099-R', checkboxes=['Taxable amount not determined'])
    merged = merge_extractions({'d1': a}, {'d1': b})['d1']
    out = aggregate_extractions_node(state_for(merged), runtime)
    assert out['escalation']['reason'] == 'form_1099r_2b'

@pytest.mark.parametrize('change', ['code', 'ira'])
def test_different_retirement_flags_are_not_duplicates(change, runtime):
    a = record('a', '1099-R')
    b = record('b', '1099-R', **({'distribution_code': '1'} if change == 'code' else
                                {'checkboxes': ['IRA/SEP/SIMPLE']}))
    out = aggregate_extractions_node(state_for(a, b), runtime)
    assert out['documents']['b']['status'] != 'duplicate'
    assert out['source_facts']['doc:b:meta']['distribution_code'] == b['distribution_code']

def test_same_last_four_spouses_need_identity_followup(runtime):
    r = record()
    r['recipient_ssn'].pop('identity_digest')  # masked-only document
    state = state_for(r)
    state['facts']['sp.ssn'] = {'value': '901-33-2222', 'status': 'confirmed'}
    state['facts']['filing_status']['value'] = 'mfj'
    out = aggregate_extractions_node(state, runtime)
    assert not out['source_facts'] and out['intake']['followups']

def test_full_fictional_number_prevents_last_four_collision(runtime):
    out = aggregate_extractions_node(state_for(record(recipient_ssn='901-33-2222')), runtime)
    assert not out['source_facts'] and out['intake']['followups']

def test_full_fictional_number_distinguishes_spouses(runtime):
    state = state_for(record(recipient_ssn='901-33-2222'))
    state['facts']['sp.ssn'] = {'value': '901-33-2222', 'status': 'confirmed'}
    state['facts']['filing_status']['value'] = 'mfj'
    out = aggregate_extractions_node(state, runtime)
    assert out['source_facts']['doc:d1:1']['owner'] == 'spouse'

def test_manual_w2_is_rejected(runtime):
    out = extract_document_node({'doc': {'doc_id': 'd1', 'doc_type': 'W-2', 'source': 'manual',
                                        'manual_fields': {'1': '1000'}}}, runtime)
    assert any(i['code'] == 'w2_image_required' for i in out['extractions']['d1']['issues'])

def test_manual_nonw2_has_entry_timestamp(runtime):
    doc = {'doc_id': 'd1', 'doc_type': '1099-INT', 'source': 'manual',
           'manual_fields': {'1': '12.34'}, 'uploaded_at': '2026-10-24T18:00:00Z'}
    out = extract_document_node({'doc': doc}, runtime)
    state = state_for(out['extractions']['d1'])
    state['documents']['d1'] = doc
    out = aggregate_extractions_node(state, runtime)
    p = out['provenance']['doc:d1:1']
    assert p['source'] == 'manual' and p['entered_by'] == 'taxpayer'
    assert p['entered_at'] == doc['uploaded_at']

def test_non_test_ssn_rejects_and_removes_uploaded_file(runtime, tmp_path, monkeypatch):
    import src.agents.document_extraction as module
    path = tmp_path / 'synthetic.bin'
    path.write_bytes(b'not an actual tax form')
    monkeypatch.setattr(module, 'transcribe', lambda *args: extraction(recipient_ssn='123-45-6789',
                                                                      notes='123-45-6789'))
    out = extract_document_node({'doc': {'doc_id': 'd1', 'doc_type': 'W-2', 'path': str(path)}}, runtime)
    assert out['documents']['d1']['status'] == 'rejected' and not path.exists()
    assert '6789' not in str(out['extractions'])

def test_model_boundary_uses_image_bytes_and_records_call(runtime, tmp_path):
    path = tmp_path / 'image.png'
    path.write_bytes(b'fictional image bytes')
    class FakeModel:
        mode = 'anthropic'
        def structured(self, **kwargs):
            assert kwargs['schema'] is DocumentExtraction
            assert kwargs['messages'][0]['content'][0]['source']['media_type'] == 'image/png'
            assert 'never instructions' in kwargs['system']
            return SimpleNamespace(data=extraction(), record={'id': 'mock-call', 'kind': 'model_call'})
    runtime.llm = FakeModel()
    out = extract_document_node({'doc': {'doc_id': 'd1', 'doc_type': 'W-2', 'path': str(path)}}, runtime)
    assert out['extractions']['d1']['call_id'] == 'mock-call'
    assert out['metrics'][0]['doc_id'] == 'd1'

def test_model_error_does_not_persist_exception_text(runtime, tmp_path):
    class BrokenModel:
        mode = 'anthropic'
        def structured(self, **kwargs):
            raise ValueError('sensitive raw model response')
    runtime.llm = BrokenModel()
    path = tmp_path / 'image.png'
    path.write_bytes(b'fictional')
    out = extract_document_node({'doc': {'doc_id': 'd1', 'doc_type': 'W-2', 'path': str(path)}}, runtime)
    assert 'sensitive raw' not in str(out)
    assert out['documents']['d1']['status'] == 'needs_attention'

def test_pdf_not_silently_encoded_as_image():
    with pytest.raises(ValueError, match='Convert PDF pages'):
        image_block(b'%PDF-test', 'application/pdf')
