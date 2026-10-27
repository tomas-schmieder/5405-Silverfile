from src.provenance import lineage_gaps, resolve

def test_transitive_missing_source_is_detected():
    p = {'line:16': {'value': '100', 'inputs': {'base': {'ref': 'line:15'}}},
         'line:15': {'value': '1000', 'inputs': {'income': {'ref': 'doc:gone:1'}}}}
    gaps = lineage_gaps({'16': {'value': '100'}}, p, ['16'])
    assert any('doc:gone:1' in x['problem'] for x in gaps)

def test_cycle_is_detected_without_recursion_error():
    p = {'line:16': {'value': '100', 'inputs': {'self': {'ref': 'line:16'}}}}
    assert 'cyclic' in lineage_gaps({'16': {'value': '100'}}, p, ['16'])[0]['problem']
    assert resolve(p, 'line:16')['children'][0]['record'] == p['line:16']

def test_complete_chain_is_valid():
    p = {'line:16': {'value': '100', 'inputs': {'income': {'refs': ['doc:a:1', 'fact:amount']}}},
         'doc:a:1': {'kind': 'document', 'value': '1000'},
         'fact:amount': {'kind': 'direct_input', 'value': '200'}}
    assert not lineage_gaps({'16': {'value': '100'}}, p, ['16'])

def test_extra_populated_line_also_needs_provenance():
    gaps = lineage_gaps({'35a': {'value': '100'}}, {}, [])
    assert gaps == [{'line': '35a', 'problem': 'no provenance record'}]
