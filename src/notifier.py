"""Notification dispatcher with convention-based formatter discovery."""

import importlib
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

FORMATTERS_DIR = Path(__file__).parent / "formatters"


def discover_formatters() -> list[dict]:
    """Scan src/formatters/ and load formatters whose env var is set and not disabled."""
    formatters = []

    for py_file in sorted(FORMATTERS_DIR.glob("*.py")):
        name = py_file.stem
        if name.startswith("_"):
            continue

        env_key = f"{name.upper()}_WEBHOOK"
        enabled_key = f"{name.upper()}_ENABLED"

        # Explicitly disabled
        if os.environ.get(enabled_key, "").lower() == "false":
            continue

        webhook_url = os.environ.get(env_key)
        if not webhook_url:
            continue

        try:
            module = importlib.import_module(f"src.formatters.{name}")
            formatters.append({
                "name": name,
                "module": module,
                "webhook_url": webhook_url,
            })
            logger.info(f"Loaded formatter: {name}")
        except Exception as e:
            logger.error(f"Failed to load formatter {name}: {e}")

    return formatters


def send_notifications(formatters: list[dict], changes: dict[str, set[str]]) -> None:
    """Send aggregated notification to all enabled formatters."""
    if not changes:
        return

    for formatter in formatters:
        try:
            payload = formatter["module"].format_message(changes)
            if payload is not None:
                formatter["module"].send(payload, formatter["webhook_url"])
                logger.info(f"Sent notification via {formatter['name']}")
        except Exception as e:
            logger.error(f"Failed to send via {formatter['name']}: {e}")
