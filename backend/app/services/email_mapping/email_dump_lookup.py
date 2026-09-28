"""Normalize email values and index dump records."""
import pandas as pd


def normalize(value):
    return str(value).strip().lower() if pd.notna(value) else ""


def build_email_lookup(dump, dump_email_column):
    lookup = {}
    for _, row in dump.iterrows():
        email = normalize(row[dump_email_column])
        if email:
            lookup.setdefault(email, []).append(row)
    return lookup

# Purpose: Normalize email values and index dump records.
# Its public interface includes normalize, build_email_lookup.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.email_mapping.email_mapping_pipeline, app.services.email_mapping.email_row_classification.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
