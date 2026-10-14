"""Shared dataframe preparation and column lookup helpers."""


def prepare_source(frame):
    return frame.fillna('').astype(str).apply(lambda column: column.str.strip())


def find_column(source, header):
    return next(
        (column for column in source.columns if str(column).strip() == header),
        None,
    )
