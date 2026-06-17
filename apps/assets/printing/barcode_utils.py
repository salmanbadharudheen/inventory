"""Shared helpers for barcode payload generation."""

from __future__ import annotations


def barcode_payload(asset_tag: str) -> str:
    """Return the shorter payload used only for Code128 barcode generation.

    The label can still display the full asset tag, but the barcode itself can
    encode a shorter value to reduce symbol width and bar count.
    """
    value = (asset_tag or '').strip()
    if not value:
        return ''

    if value.upper().startswith('TE-'):
        value = value[3:]

    return value.replace('-', '')