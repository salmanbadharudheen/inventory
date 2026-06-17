"""Renderer registry — maps a print mode string to a renderer instance."""

from __future__ import annotations

from .base import LabelRenderer
from .pdf_renderer import PDFLabelRenderer
from .zpl_renderer import ZPLLabelRenderer
from .tspl_renderer import TSPLLabelRenderer
from .weasy_renderer import WeasyLabelRenderer


# Lazily instantiated singletons keyed by mode.
_RENDERERS: dict[str, LabelRenderer] = {
    # Use Weasy renderer for server-side PDF generation where available.
    'pdf': WeasyLabelRenderer(),
    'zpl': ZPLLabelRenderer(),
    'tspl': TSPLLabelRenderer(),
    'weasy': WeasyLabelRenderer(),
}

DEFAULT_MODE = 'pdf'


def get_renderer(mode: str | None = None) -> LabelRenderer:
    """Return the renderer for ``mode`` (defaults to PDF)."""
    return _RENDERERS.get((mode or DEFAULT_MODE).strip().lower(), _RENDERERS[DEFAULT_MODE])


def available_modes() -> list[str]:
    return list(_RENDERERS.keys())
