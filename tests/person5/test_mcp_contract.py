from src.tools.mcp_client import TaxToolClient
from src.tools import tax_calculations as tc

def test_real_stdio_tool_accepts_rules_zero_tolerance():
    client=TaxToolClient()
    try:
        client.start()
        r=client.call('compare_amounts', {'label':'wages','document_amount':'46850','stated_amount':'46000','abs_tolerance':'0','rel_tolerance':'0'})
        assert r['outputs']['material'] is True
        assert r['call_id'] and r['transport'] != 'in-process (unit test)'
    finally:
        client.close()

def test_qualified_dividend_tax_is_not_exempt_from_audit():
    r=tc.verify_return({'15':'50000','3a':'2000','3b':'2000','16':'99999'},'single',1)
    assert any(f['check']=='line16_tax' for f in r['outputs']['findings'])

def test_negative_agi_flows_to_zero_taxable_income():
    assert tc.deductions_and_taxable_income('-1000','17750','0','6000')['outputs']['15']=='0'
    assert tc.enhanced_senior_deduction('single','-1000',True,False)['outputs']['13b']=='6000'
