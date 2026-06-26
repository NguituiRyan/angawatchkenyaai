"""Masumi network integration: identity, discovery, escrow payment, audit trail.

A single MasumiClient facade with two backends (real preprod via the masumi SDK,
or a deterministic clearly-LABELED mock). Mocks are never hidden.
"""
from masumi_integration.client import build_masumi_client  # noqa: F401
