import logging
import os

def configure_logging() -> None:
    """
    Minimal, production-lean logging configuration.
    Uses LOG_LEVEL env var if set; defaults to INFO.
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Avoid double-configuring if uvicorn reloads
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
