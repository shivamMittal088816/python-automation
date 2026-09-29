"""Match input section names to database section identifiers."""


def normalize_section(value):
    return ' '.join(str(value or '').split()).casefold()


def apply_section_ids(output, database_sections):
    """Backward-compatible entry point for section preview sanity and mapping."""
    from app.services.bulk_reg_preview_sanity.section import apply_section_ids as check
    return check(output, database_sections)

# Purpose: Match input section names to database section identifiers.
# Its public interface includes normalize_section, apply_section_ids.
# It keeps declarative conversion rules separate from orchestration and HTTP code.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.bulk_registration.conversion_routes.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
