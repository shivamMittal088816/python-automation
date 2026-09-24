"""Normalize admission-mapping names; these rules are separate from email first-name matching."""

import pandas as pd

def school_first_name(value, name_is_full):
    # Full-name input contributes its first word; first-name input uses the whole cell.
    name = str(value).strip().lower() if pd.notna(value) else ""
    return (name.split()[0] if name else "") if name_is_full else name
