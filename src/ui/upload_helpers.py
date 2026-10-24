"""Filename suggestions only; extraction must verify document identity."""

def guess_form(file_name: str) -> str | None:
    """A starting guess from the file name; the taxpayer can change it, and extraction checks the form itself."""
    name = "".join(ch for ch in file_name.upper() if ch.isalnum())
    for marker, doc_type in (("SSA", "SSA-1099"), ("1099DIV", "1099-DIV"), ("DIV", "1099-DIV"),
                             ("1099INT", "1099-INT"), ("1099R", "1099-R"), ("W2", "W-2")):
        if marker in name:
            return doc_type
    return None
