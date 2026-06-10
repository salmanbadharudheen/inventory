"""
Label printing service layer.

Provides a renderer-agnostic pipeline for turning asset data into printable
label output. The current production renderer is :class:`PDFLabelRenderer`
(vector PDF via ReportLab), which is ideal for thermal / sticker printers
because it keeps barcodes and QR codes as vector graphics at exact physical
dimensions (no browser scaling, no rasterisation).

The layer is intentionally pluggable so future renderers can be added without
touching the views:

* ``pdf``  -> :class:`PDFLabelRenderer`  (implemented)
* ``zpl``  -> :class:`ZPLLabelRenderer`  (scaffold, Zebra printers)
* ``tspl`` -> :class:`TSPLLabelRenderer` (scaffold, TSC printers)

Use :func:`get_renderer` to obtain a renderer for a given mode.
"""

from .base import (
    LABEL_SIZES,
    DEFAULT_SIZE_KEY,
    LabelData,
    LabelSpec,
    LabelRenderer,
    resolve_size,
)
from .registry import get_renderer, available_modes

__all__ = [
    'LABEL_SIZES',
    'DEFAULT_SIZE_KEY',
    'LabelData',
    'LabelSpec',
    'LabelRenderer',
    'resolve_size',
    'get_renderer',
    'available_modes',
]
