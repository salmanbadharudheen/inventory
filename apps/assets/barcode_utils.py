"""Shared helpers for barcode payload generation."""

from __future__ import annotations
from typing import Any


def barcode_payload(asset_or_tag: Any) -> str:
    """Return the canonical barcode payload for a printable asset tag.

    We keep the barcode value identical to the asset tag itself so the browser
    print flow, PDF output, and mobile lookup all resolve the same identifier.
    The function accepts either an asset model instance (preferred) or a plain
    asset tag string (best-effort fallback).
    """
    if hasattr(asset_or_tag, 'asset_tag'):
        tag = (getattr(asset_or_tag, 'asset_tag', '') or '').strip()
    else:
        tag = (asset_or_tag or '').strip()

    return tag
