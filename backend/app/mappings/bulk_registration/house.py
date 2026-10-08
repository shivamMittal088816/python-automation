"""Replace supplied house names with their database identifiers."""


def apply_house_ids(frame, database_houses):
    lookup = {}
    for house_id, name in database_houses:
        key = str(name or '').strip().casefold()
        index = '' if house_id is None else str(house_id).strip()
        if key and index:
            lookup.setdefault(key, index)
    values = frame['house'].fillna('').astype(str).str.strip()
    frame.attrs['unresolved_house_positions'] = [
        position for position, value in enumerate(values)
        if value and value.casefold() not in lookup
    ]
    # Unknown names stay visible for correction through the input sanity check.
    frame['house'] = values.map(lambda value: lookup.get(value.casefold(), value))
