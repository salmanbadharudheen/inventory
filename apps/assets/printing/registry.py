"""Renderer registry — maps a print mode string to a renderer instance."""

from __future__ import annotations

from .base import LabelRenderer
from .zpl_renderer import ZPLLabelRenderer
from .tspl_renderer import TSPLLabelRenderer
from .weasy_renderer import WeasyLabelRenderer


# Lazily instantiated singletons keyed by mode.
_RENDERERS: dict[str, LabelRenderer] = {
    'zpl': ZPLLabelRenderer(),
    'tspl': TSPLLabelRenderer(),
    'weasy': WeasyLabelRenderer(),
}

DEFAULT_MODE = 'pdf'


def get_renderer(mode: str | None = None) -> LabelRenderer:
    """Return the renderer for ``mode`` (defaults to PDF)."""
    key = (mode or DEFAULT_MODE).strip().lower()
    # Prefer WeasyPrint for PDF when available
    if key == 'pdf':
        try:
            # If weasy is available, use it
            from .weasy_renderer import WeasyLabelRenderer as _W
            # instantiate lazily and cache
            if 'pdf' not in _RENDERERS:
                _RENDERERS['pdf'] = _W()
            return _RENDERERS['pdf']
        except Exception:
            # Fall back to ReportLab-based renderer only when needed.
            try:
                from .pdf_renderer import PDFLabelRenderer as _P
                if 'pdf' not in _RENDERERS:
                    _RENDERERS['pdf'] = _P()
                return _RENDERERS['pdf']
            except Exception:
                raise NotImplementedError('No PDF renderer available in this environment.')

    return _RENDERERS.get(key, _RENDERERS.get(DEFAULT_MODE))


def available_modes() -> list[str]:
    return list(_RENDERERS.keys())
