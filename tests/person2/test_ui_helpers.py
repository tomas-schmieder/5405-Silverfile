import pytest

from src.ui.upload_helpers import guess_form as _guess_form


@pytest.mark.parametrize("name, form", [
    ("W2_clean_2025.pdf", "W-2"), ("w2_image_1.png", "W-2"), ("1099_DIV_2025.pdf", "1099-DIV"),
    ("1099_R_IRA_2025.pdf", "1099-R"), ("1099-INT bank.jpg", "1099-INT"),
    ("SSA-1099_Example_2_Overpayment.pdf", "SSA-1099"), ("scan_0001.jpg", None),
])
def test_form_type_guessed_from_file_name(name, form):
    assert _guess_form(name) == form
