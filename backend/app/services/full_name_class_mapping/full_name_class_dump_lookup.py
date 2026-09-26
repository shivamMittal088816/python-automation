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
