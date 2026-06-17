"""Backward-compatible re-export of the barcode payload helper.

The implementation now lives in :mod:`apps.assets.barcode_utils` so that
barcode generation does not depend on the printing package (which imports
ReportLab).
"""

from __future__ import annotations

from ..barcode_utils import barcode_payload

__all__ = ['barcode_payload']