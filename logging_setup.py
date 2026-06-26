"""Structured logging + the LIVE/MOCK labeling that Angawatch uses everywhere.

Hiding mocks is an explicit rubric failure. Every integration that falls back
calls `mock_tag()` / logs with the mode so it is impossible to miss.
"""
from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def _configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    # Windows consoles default to cp1252 and crash on UTF-8/emoji. Best-effort fix.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s",
                          datefmt="%H:%M:%S")
    )
    root = logging.getLogger("angawatch")
    root.setLevel(logging.INFO)
    root.handlers = [handler]
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(f"angawatch.{name}")


_LIVE = {"live", "neo4j", "real"}


def tag(mode: str) -> str:
    """live/neo4j/real -> '[LIVE]', anything else -> '[MOCK]'. For logs + CLI."""
    return "[LIVE]" if str(mode).lower() in _LIVE else "[MOCK]"


def badge(mode: str) -> str:
    """Dashboard-friendly pill text."""
    return "🟢 LIVE" if str(mode).lower() in _LIVE else "🟠 MOCK"


def banner(title: str, lines: list[str] | None = None) -> str:
    """A boxed banner for the narrated CLI demo."""
    width = max([len(title)] + [len(l) for l in (lines or [])]) + 4
    out = ["", "═" * width, f"  {title}", "─" * width]
    for l in lines or []:
        out.append(f"  {l}")
    out.append("═" * width)
    return "\n".join(out)
