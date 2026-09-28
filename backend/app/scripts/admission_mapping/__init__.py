"""Supported admission mapping imports and script/module CLI entry points."""

# Purpose: Supported admission mapping imports and script/module CLI entry points.
# It primarily establishes package exports, constants, or module-level configuration.
# It supports explicit command-line or maintenance execution outside HTTP requests.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: developers or the application server invoke this module as an entry point.
# It is intentionally callable without requiring another backend module to import it.
# Tests and higher-level workflows exercise this behavior through its public callers.
