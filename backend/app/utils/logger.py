# Configure the shared Loguru logger, rotating log files and retention period.
# Importing this module registers the file output.

from pathlib import Path

from loguru import logger


# =====================================
# CREATE LOG DIRECTORY
# =====================================

Path("logs").mkdir(
    exist_ok=True
)


# =====================================
# LOGGER CONFIG
# =====================================

logger.add(
    "logs/app.log",

    rotation="10 MB",

    retention="10 days",

    level="INFO",

    enqueue=True,

    backtrace=True,

    diagnose=True
)


__all__ = ["logger"]

# Purpose: Configures the reusable application logger and log destinations.
# It primarily establishes package exports, constants, or module-level configuration.
# It supplies reusable helpers without owning endpoint or workflow state.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: this module is currently available as a focused backend building block.
# No other application module directly imports it at present.
# Tests and higher-level workflows exercise this behavior through its public callers.
