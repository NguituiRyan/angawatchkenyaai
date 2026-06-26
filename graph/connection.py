"""Neo4j driver lifecycle. Safe to import even when `neo4j` isn't installed."""
from __future__ import annotations

from logging_setup import get_logger

log = get_logger("graph.conn")


def get_driver(uri: str, user: str, password: str):
    """Return a verified Neo4j driver, or raise. Caller handles fallback."""
    from neo4j import GraphDatabase  # local import: optional dependency

    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def can_connect(uri: str | None, user: str, password: str | None) -> bool:
    if not (uri and password):
        return False
    try:
        d = get_driver(uri, user, password)
        d.close()
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Neo4j not reachable (%s) — will use in-memory fallback", exc)
        return False
