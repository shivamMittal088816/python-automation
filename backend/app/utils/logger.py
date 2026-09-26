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