"""Email mapping services."""

# Purpose: Email mapping services.
# It primarily establishes package exports, constants, or module-level configuration.
# It contains business behavior independently of FastAPI route registration.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: Python imports this package marker while resolving its child modules.
# Consumers normally import the focused modules inside this package directly.
# Tests and higher-level workflows exercise this behavior through its public callers.
