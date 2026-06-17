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
        # Try Weasy first, but only if it's actually usable (weasy_renderer exposes HTML)
        try:
            import importlib
            _weasy_mod = importlib.import_module('apps.assets.printing.weasy_renderer')
            if getattr(_weasy_mod, 'HTML', None) is not None:
                _W = getattr(_weasy_mod, 'WeasyLabelRenderer')
                if 'pdf' not in _RENDERERS:
                    _RENDERERS['pdf'] = _W()
                return _RENDERERS['pdf']
        except Exception:
            # proceed to try reportlab-backed renderer
            pass

        # Fall back to ReportLab-based renderer only when available.
        try:
            from .pdf_renderer import PDFLabelRenderer as _P
            if 'pdf' not in _RENDERERS:
                _RENDERERS['pdf'] = _P()
            return _RENDERERS['pdf']
        except Exception:
            pass

        from .pillow_pdf_renderer import PillowPDFLabelRenderer as _PillowPDF
        if 'pdf' not in _RENDERERS:
            _RENDERERS['pdf'] = _PillowPDF()
        return _RENDERERS['pdf']

    return _RENDERERS.get(key, _RENDERERS.get(DEFAULT_MODE))


def available_modes() -> list[str]:
    return list(_RENDERERS.keys())
