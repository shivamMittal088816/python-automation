"""School identity inference and class/section statistics."""
import pandas as pd


def inferred_school_index(rows):
    if "user_edu_school" not in rows:
        return ""
    values = {str(value).strip() for value in rows["user_edu_school"]
              if pd.notna(value) and str(value).strip()}
    return next(iter(values)) if len(values) == 1 else ""


def class_section_table(rows, class_column, section_column, package_column=None,
                        class_offset=0, student_id_column=None):
    """Return one row per class with unique sections, packages and student count."""
    if class_column == section_column:
        raise ValueError("Choose different class and section columns.")
    data = rows[[class_column, section_column]].copy()
    class_values = data[class_column].fillna("").astype(str).str.strip()
    data["Class"] = class_values.map(
        lambda value: f"Class {int(value) + class_offset}" if value.isdecimal()
        else value or "Not specified")
    data["Section"] = data[section_column].fillna("").astype(str).str.strip().replace("", "Not specified")
    if package_column is not None:
        data["Package"] = rows[package_column].fillna("").astype(str).str.strip().replace("", "Not specified")
    if student_id_column is not None:
        ids = rows[student_id_column].fillna("").astype(str).str.strip()
        data["_student_key"] = [("id", value) if value else ("row", position)
                                for position, value in enumerate(ids)]
    else:
        data["_student_key"] = [("row", position) for position in range(len(data))]
    unique_values = lambda values: ", ".join(sorted(set(values), key=str.lower))
    aggregation = {"Sections": ("Section", unique_values)}
    if package_column is not None:
        aggregation["Packages"] = ("Package", unique_values)
    aggregation["Students"] = ("_student_key", "nunique")
    overview = data.groupby("Class", sort=False, dropna=False).agg(**aggregation).reset_index()
    def class_order(label):
        value = label.removeprefix("Class ")
        return (0, int(value)) if value.isdecimal() else (1, label.lower())
    return overview.iloc[sorted(range(len(overview)),
        key=lambda position: class_order(overview.iloc[position]["Class"]))].reset_index(drop=True)


def school_class_statistics(rows, class_column, section_column):
    """Group school rows by their exact class text and list unique sections."""
    if class_column == section_column:
        raise ValueError("Choose different class and section columns.")
    data = pd.DataFrame({
        "Class": rows[class_column].fillna("").astype(str).str.strip().replace("", "Not specified"),
        "Section": rows[section_column].fillna("").astype(str).str.strip().replace("", "Not specified"),
    })
    unique_values = lambda values: ", ".join(dict.fromkeys(values))
    return data.groupby("Class", sort=False, dropna=False).agg(
        Students=("Class", "size"),
        Sections=("Section", unique_values),
    ).reset_index()


def dump_overview(rows):
    """Return unique sections for each class and the count of distinct student IDs."""
    if not {"user_edu_class", "user_edu_major"}.issubset(rows.columns):
        return None, None
    table = class_section_table(rows, "user_edu_class", "user_edu_major",
                                "user_package" if "user_package" in rows.columns else None,
                                class_offset=1,
                                student_id_column="user_id" if "user_id" in rows.columns else None)
    if "user_id" in rows.columns:
        ids = rows["user_id"].fillna("").astype(str).str.strip()
        # Blank IDs cannot establish identity, so count their rows separately.
        student_count = len({("id", value) if value else ("row", position)
                             for position, value in enumerate(ids)})
    else:
        student_count = len(rows)
    return table, student_count
