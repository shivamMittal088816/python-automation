"""Command-line admission mapping: read inputs and write three result workbooks."""

import argparse
from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.admission_mapping.admission_file_reader import read_file
from app.services.admission_mapping.admission_mapping_pipeline import map_students
from app.services.admission_mapping.admission_result_exports import build_exports

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--school", type=Path, required=True, help="School .csv or .xlsx file")
    parser.add_argument("--dump", type=Path, required=True, help="Dump .csv or .xlsx file")
    parser.add_argument("--school-sheet", help="Excel sheet name; defaults to first sheet")
    parser.add_argument("--dump-sheet", help="Excel sheet name; defaults to first sheet")
    parser.add_argument("--school-admission-column", default="admission_number")
    parser.add_argument("--dump-admission-column", default="admission_number")
    parser.add_argument("--username-column", default="user_name", help="Username column in dump; default: user_name")
    names = parser.add_mutually_exclusive_group()
    parser.add_argument("--dump-first-name-column", default="user_firstname", help="First-name column in dump")
    names.add_argument("--first-name-column", help="School first-name column; default: first_name")
    names.add_argument("--full-name-column", help="Use first word of this school full-name column")
    parser.add_argument("--output", type=Path, default=Path("admission_mapping_results.xlsx"),
                        help="Output filename prefix; writes _matched, _review and _not_matched.xlsx")
    args = parser.parse_args()

    if args.output.suffix.lower() != ".xlsx":
        parser.error("Output must be an .xlsx file.")
    output_paths = [args.output.with_name(f"{args.output.stem}_{suffix}.xlsx")
                    for suffix in ("matched", "review", "not_matched")]
    for path in output_paths:
        if path.resolve() in (args.school.resolve(), args.dump.resolve()):
            parser.error("Output must be different from both input files.")
        if path.exists():
            parser.error(f"Output already exists: {path}. Choose a new --output path.")

    try:
        result = map_students(
            read_file(args.school, args.school_sheet),
            read_file(args.dump, args.dump_sheet),
            args.school_admission_column,
            args.dump_admission_column,
            args.username_column,
            args.full_name_column or args.first_name_column or "first_name",
            name_is_full=args.full_name_column is not None,
            dump_first_name_column=args.dump_first_name_column,
        )
        exports = build_exports(result)
        print(f"Rows in duplicate groups: {result.attrs['duplicate_rows']}; rows dropped: {result.attrs['dropped_rows']}")
        for path, export in zip(output_paths, exports.values()):
            path.write_bytes(export["data"])
            print(f"Saved: {path.resolve()} ({export['count']} students)")
    except (ValueError, OSError, KeyError, ImportError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
