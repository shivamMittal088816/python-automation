"""Normalize admission-mapping names; these rules are separate from email first-name matching."""

import pandas as pd

def school_first_name(value, name_is_full):
    # Full-name input contributes its first word; first-name input uses the whole cell.
    name = str(value).strip().lower() if pd.notna(value) else ""
    return (name.split()[0] if name else "") if name_is_full else name

# Purpose: Normalize admission-mapping names; these rules are separate from email first-name matching.
# Its public interface includes school_first_name.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.admission_mapping.admission_row_classification.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
