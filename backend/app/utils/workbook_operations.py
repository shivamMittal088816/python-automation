"""Workbook conversion, status normalization and manual row transfers."""
from io import BytesIO
from pathlib import Path
import pandas as pd
from app.services.admission_mapping.admission_workbook import build_workbook


def move_students(exports, filename, selected_rows, destination):
    """Rebuild both workbooks before publishing the manual classification to session state."""
    statuses = {"matched.xlsx": "Matched", "not_matched.xlsx": "Not Matched", "review.xlsx": "Review"}
    if destination not in statuses or filename == destination:
        raise ValueError("Choose a different Matched, Not matched or Review destination.")
    exports = remove_original_columns(exports)
    rows = pd.read_excel(BytesIO(exports[filename]["data"]), dtype=str, keep_default_na=False)
    # Selection contains zero-based table positions, not admission numbers or database IDs.
    # Position-based movement keeps identical-looking school records independent.
    positions = sorted(set(selected_rows))
    if not positions or any(i < 0 or i >= len(rows) for i in positions):
        raise ValueError("Select valid records to move.")
    moved = rows.iloc[positions].copy()
    source_label = {
        "matched.xlsx": "Matched",
        "review.xlsx": "Review",
        "not_matched.xlsx": "Not Matched",
        "new_students.xlsx": "New students",
    }.get(filename, filename)
    moved["mapping_status"] = (
        f"{statuses[destination]} — Student manually moved from preview: "
        f"{source_label} to {statuses[destination]}"
    )
    moved = moved.drop(columns="mapping_reason", errors="ignore")
    remaining = rows.drop(rows.index[positions])
    existing = exports.get(destination)
    if existing:
        previous = pd.read_excel(BytesIO(existing["data"]), dtype=str, keep_default_na=False)
        moved = pd.concat([previous, moved], ignore_index=True)
    # Build a replacement dictionary first; the caller publishes it to session state only on success.
    updated = dict(exports)
    updated[filename] = build_workbook(remaining, "Results")
    updated[destination] = build_workbook(moved, statuses[destination])
    return updated


def remove_original_columns(exports):
    updated = dict(exports)
    for filename, export in exports.items():
        rows = pd.read_excel(BytesIO(export["data"]), dtype=str, keep_default_na=False)
        retired = [name for name in ("mapping_original_reason", "mapping_original_status")
                   if name in rows.columns]
        if "mapping_reason" in rows.columns:
            rows["mapping_status"] = rows["mapping_status"] + " — " + rows["mapping_reason"]
            retired.append("mapping_reason")
        if retired:
            updated[filename] = build_workbook(rows.drop(columns=retired), "Results")
    return updated


def convert_dump(data, name, output_format, sheet=0):
    """Preserve original bytes when possible and read identifiers as text."""
    suffix = Path(name).suffix.lower()
    if suffix == f".{output_format}":
        return data
    if suffix == ".xlsx":
        rows = pd.read_excel(BytesIO(data), sheet_name=sheet, dtype=str, keep_default_na=False)
    else:
        rows = pd.read_csv(BytesIO(data), dtype=str, keep_default_na=False)
    if output_format == "csv":
        return rows.to_csv(index=False).encode("utf-8-sig")
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        rows.to_excel(writer, index=False, sheet_name="Dump")
        # Dump values are data, including strings that start with '='.
        for row in writer.sheets["Dump"]:
            for cell in row:
                if cell.data_type == "f":
                    cell.data_type = "s"
    return buffer.getvalue()
