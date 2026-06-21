"""Shared helpers for barcode payload generation."""

from __future__ import annotations
from typing import Any


def _base36_to_int(segment: str) -> int | None:
    """Convert an uppercase base36 segment to int, returning None if invalid."""
    value = (segment or '').strip().upper()
    if not value:
        return None

    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    acc = 0
    for ch in value:
        idx = alphabet.find(ch)
        if idx < 0:
            return None
        acc = (acc * 36) + idx
    return acc


def derive_new_asset_barcode_payload(asset_or_tag: Any) -> str:
    """Build a shorter numeric payload for newly created assets when possible.

    Compact mode targets the default asset tag shape: ``CC-CCC-SEQ-YY``.
    It returns an 18-digit numeric payload so Code128 can use dense numeric
    encoding (fewer visual bars) while preserving uniqueness.

    If the incoming tag does not match the expected shape, the function falls
    back to the raw tag to avoid any scanning/lookup regressions.
    """
    if hasattr(asset_or_tag, 'asset_tag'):
        tag = (getattr(asset_or_tag, 'asset_tag', '') or '').strip().upper()
        org = getattr(asset_or_tag, 'organization', None)
        separator = (getattr(org, 'tag_separator', None) or '-').strip() or '-'
    else:
        tag = (asset_or_tag or '').strip().upper()
        separator = '-'

    if not tag:
        return ''

    parts = tag.split(separator)
    if len(parts) != 4:
        return tag

    company_seg, category_seg, sequence_seg, year_seg = parts
    if len(company_seg) != 2 or len(category_seg) != 3 or len(year_seg) != 2:
        return tag
    if not year_seg.isdigit():
        return tag

    company_num = _base36_to_int(company_seg)
    category_num = _base36_to_int(category_seg)
    sequence_num = _base36_to_int(sequence_seg)
    if company_num is None or category_num is None or sequence_num is None:
        return tag

    return f"{company_num:04d}{category_num:05d}{sequence_num:07d}{int(year_seg):02d}"


def barcode_payload(asset_or_tag: Any) -> str:
    """Return the canonical barcode payload for a printable asset tag.

    We keep the barcode value identical to the asset tag itself so the browser
    print flow, PDF output, and mobile lookup all resolve the same identifier.
    The function accepts either an asset model instance (preferred) or a plain
    asset tag string (best-effort fallback).
    """
    if hasattr(asset_or_tag, 'asset_tag'):
        override_payload = (getattr(asset_or_tag, 'barcode_payload_value', '') or '').strip()
        if override_payload:
            return override_payload
        tag = (getattr(asset_or_tag, 'asset_tag', '') or '').strip()
    else:
        tag = (asset_or_tag or '').strip()

    return tag
