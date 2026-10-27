from pathlib import Path
import hashlib,json
import pymupdf
from src.agents.eligibility_rules import registry
ROOT=Path(__file__).resolve().parents[2]
def test_reference_hashes_and_identity_checks():
    manifest=json.loads((ROOT/'data/source_manifest.json').read_text())
    for source in manifest['sources']:
        path=ROOT/source['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
        if path.suffix=='.pdf':
            assert source['verified'] and all(source['identity_checks'].values())
def test_registry_references_exist_and_pages_are_in_range():
    sources={s['id']:s for s in json.loads((ROOT/'data/source_manifest.json').read_text())['sources']}
    for rule in registry().values():
        for c in rule['citations']:
            if c['doc']=='assignment': continue
            assert c['doc'] in sources
            assert 1 <= c['page'] <= sources[c['doc']]['pages']
