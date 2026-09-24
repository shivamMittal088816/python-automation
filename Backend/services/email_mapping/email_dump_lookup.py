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
