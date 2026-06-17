"""Shared helpers for barcode payload generation."""

from __future__ import annotations
import re
from typing import Any


def barcode_payload(asset_or_tag: Any) -> str:
    """Return a compact payload for Code128 barcodes.

    Preferred form (Option B): one-char org + one-char category + numeric suffix.
    Examples:
      - asset with org 'tel' and category 'c12' and tag 'TE-ITX-000126' -> 'TC000126'

    The function accepts either an asset model instance (preferred) or a
    plain asset tag string (best-effort fallback).
    """
    # If an asset instance is passed, try to extract org/category and tag
    tag = None
    org_prefix = ''
    cat_prefix = ''

    if hasattr(asset_or_tag, 'asset_tag'):
        asset = asset_or_tag
        tag = (getattr(asset, 'asset_tag', '') or '').strip()
        org = getattr(asset, 'organization', None) or getattr(asset, 'company', None)
        if org is not None:
            slug = getattr(org, 'slug', None) or getattr(org, 'name', None)
            if slug:
                org_prefix = str(slug).strip()[0].upper()
        category = getattr(asset, 'category', None)
        if category is not None:
            cat_code = getattr(category, 'code', None) or getattr(category, 'name', None) or getattr(category, 'id', None)
            if cat_code:
                cat_prefix = str(cat_code).strip()[0].upper()
    else:
        tag = (asset_or_tag or '').strip()

    if not tag:
        return ''

    # Normalise: remove common TE- prefix and dashes
    if tag.upper().startswith('TE-'):
        tag = tag[3:]
    norm = tag.replace('-', '')

    # Extract the numeric suffix (last continuous digit sequence)
    nums = re.findall(r"(\d+)", norm)
    suffix = nums[-1] if nums else ''

    # Fallback prefixes when not available from asset
    if not org_prefix:
        # use first letter of normalized tag as a weak org proxy
        org_prefix = (norm[0].upper() if norm else 'X')
    if not cat_prefix:
        cat_prefix = 'C'

    if not suffix:
        # if no numeric suffix, use trimmed alphanum up to 10 chars
        payload = (org_prefix + cat_prefix + re.sub(r'[^A-Za-z0-9]', '', norm))[:12]
    else:
        # preserve original numeric length
        payload = f"{org_prefix}{cat_prefix}{suffix}"

    return payload
