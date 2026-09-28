"""Normalize concatenated values and index the dump."""
from collections import defaultdict

import pandas as pd


def value(item):
    return str(item).strip().lower() if pd.notna(item) else ""


def build_full_name_class_lookup(dump):
    if "generated_col" not in dump.columns:
        raise ValueError("The dump has no generated_col column.")

    lookup = defaultdict(list)
    for _, user in dump.iterrows():
        key = value(user["generated_col"])
        if key:
            lookup[key].append(user)

    return lookup

# Purpose: Normalize concatenated values and index the dump.
# Its public interface includes value, build_full_name_class_lookup.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.full_name_class_mapping.full_name_class_mapping_pipeline, app.services.full_name_class_mapping.full_name_class_row_classification.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
