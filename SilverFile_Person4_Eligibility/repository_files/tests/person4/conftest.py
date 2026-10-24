"""Contract stub only: no production tax engine or MCP server is installed by this stage."""
from decimal import Decimal
from types import SimpleNamespace
import pytest
from src.agents.base import Runtime
from src.config import Settings
class ContractTools:
    def call(self, name, args):
        if name == 'aggregate_amounts':
            total = sum((Decimal(x['amount']) for x in args['items']), Decimal(0))
            return {'exact_total': format(total,'.2f'), 'call_id': 'stub-sum', 'tool': name, 'trace': [], 'transport': 'test-stub'}
        if name == 'compare_amounts':
            assert args['abs_tolerance'] == '0' and args['rel_tolerance'] == '0'
            different = Decimal(args['document_amount']) != Decimal(args['stated_amount'])
            return {'outputs': {'material': different}, 'call_id': 'stub-compare', 'tool': name, 'trace': ['Test-only exact comparison'], 'transport': 'test-stub'}
        raise AssertionError('Unexpected tool: '+name)
@pytest.fixture
def runtime(tmp_path):
    return Runtime(llm=SimpleNamespace(mode='offline'),tools=ContractTools(),settings=Settings(llm_mode='offline',var_dir=tmp_path/'var'),now=lambda:'2026-10-24T20:00:00Z')
