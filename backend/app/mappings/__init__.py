"""Declarative data-mapping rules used by backend services."""

# Purpose: Declarative data-mapping rules used by backend services.
# It primarily establishes package exports, constants, or module-level configuration.
# It keeps declarative conversion rules separate from orchestration and HTTP code.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: Python imports this package marker while resolving its child modules.
# Consumers normally import the focused modules inside this package directly.
# Tests and higher-level workflows exercise this behavior through its public callers.
