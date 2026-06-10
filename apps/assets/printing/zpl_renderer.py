"""Zebra ZPL label renderer (scaffold).

Placeholder for direct Zebra (ZPL II) printer support. Implementing this will
let the system stream native ZPL to networked / USB Zebra printers instead of
producing a PDF, which is the most reliable path for high-volume thermal
printing. Left as a scaffold so the service layer is ready without committing
to a hardware integration yet.
"""

from __future__ import annotations

from .base import LabelRenderer, LabelData, LabelSpec


class ZPLLabelRenderer(LabelRenderer):
    """Not yet implemented — emits native Zebra ZPL II."""

    content_type = 'text/plain'
    file_extension = 'zpl'
    mode = 'zpl'

    def render(self, labels: list[LabelData], spec: LabelSpec) -> bytes:
        raise NotImplementedError(
            'ZPL rendering is not implemented yet. Use mode="pdf" for now.'
        )
