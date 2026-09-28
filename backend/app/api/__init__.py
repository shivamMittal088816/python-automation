# Purpose: Marks app.api as the package for shared workflow HTTP support code.
# It separates reusable API-layer concerns from endpoint definitions in app.routes.
# The package contains session, persistence, validation, snapshot, and response helpers.
# Keeping these helpers here prevents route modules from owning business-independent plumbing.
# It has no startup side effects and does not register FastAPI routes by itself.
# Used by: route modules import the individual helpers contained in this package.
# Workflow services also import narrowly scoped invalidation helpers when required.
# Tests import selected API helpers directly to verify their isolated behavior.
