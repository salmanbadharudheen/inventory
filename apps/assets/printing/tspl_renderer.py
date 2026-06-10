"""TSC TSPL label renderer (scaffold).

Placeholder for direct TSC (TSPL/TSPL2) printer support. Implementing this
will let the system stream native TSPL to TSC thermal printers. Left as a
scaffold so the service layer is future-ready.
"""

from __future__ import annotations

from .base import LabelRenderer, LabelData, LabelSpec


class TSPLLabelRenderer(LabelRenderer):
    """Not yet implemented — emits native TSC TSPL."""

    content_type = 'text/plain'
    file_extension = 'tspl'
    mode = 'tspl'

    def render(self, labels: list[LabelData], spec: LabelSpec) -> bytes:
        raise NotImplementedError(
            'TSPL rendering is not implemented yet. Use mode="pdf" for now.'
        )
