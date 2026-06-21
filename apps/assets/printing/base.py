"""Core data structures and the abstract renderer contract for label printing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ── Supported sticker sizes (width_mm, height_mm) ──────────────────────────
# Keys mirror the values used by the front-end size selector in
# templates/assets/print_label.html so the same identifiers flow end-to-end.
LABEL_SIZES = {
    '133x19': (133.0, 19.0),   # continuous roll, 133mm x 19mm
    '2x1':    (50.8, 25.4),    # 2in  x 1in    (default)
    '2x1.5':  (50.8, 38.1),    # 2in  x 1.5in
    '3x1':    (76.2, 25.4),    # 3in  x 1in
    '3x2':    (76.2, 50.8),    # 3in  x 2in
}

DEFAULT_SIZE_KEY = '2x1'

# Minimum rendering resolution target for raster fallbacks (thermal printers
# are typically 203 or 300 dpi; we never go below this).
MIN_DPI = 300


def resolve_size(size_key: Optional[str]) -> tuple[float, float]:
    """Return ``(width_mm, height_mm)`` for a size key, falling back to default."""
    return LABEL_SIZES.get((size_key or '').strip(), LABEL_SIZES[DEFAULT_SIZE_KEY])


@dataclass
class LabelData:
    """Everything needed to render a single asset label."""

    asset_tag: str
    barcode_tag: str = ''
    org_name: str = ''
    asset_name: str = ''
    category: str = ''
    location: str = ''
    logo_path: Optional[str] = None  # storage-relative path, optional

    def safe_tag(self) -> str:
        return (self.asset_tag or '').strip()

    def safe_barcode_tag(self) -> str:
        return (self.barcode_tag or '').strip() or self.safe_tag()


@dataclass
class LabelSpec:
    """Print specification shared by all renderers."""

    size_key: str = DEFAULT_SIZE_KEY
    design: str = 'CLASSIC'
    copies: int = 1
    show_org: bool = True
    show_qr: bool = True
    show_barcode: bool = True
    show_name: bool = False
    show_category: bool = False
    show_location: bool = False
    dpi: int = MIN_DPI
    width_mm: float = field(init=False)
    height_mm: float = field(init=False)

    def __post_init__(self) -> None:
        self.width_mm, self.height_mm = resolve_size(self.size_key)
        self.design = (self.design or 'CLASSIC').upper()
        try:
            self.copies = max(1, min(int(self.copies), 100))
        except (TypeError, ValueError):
            self.copies = 1
        if self.dpi < MIN_DPI:
            self.dpi = MIN_DPI


class LabelRenderer(ABC):
    """Abstract base every concrete renderer implements."""

    #: HTTP content type of the produced payload.
    content_type: str = 'application/octet-stream'
    #: File extension (no dot) used for download filenames.
    file_extension: str = 'bin'
    #: Human-friendly mode identifier.
    mode: str = 'base'
    #: Content-Disposition: 'inline' (view/print in browser) or 'attachment'.
    disposition: str = 'inline'

    @abstractmethod
    def render(self, labels: list[LabelData], spec: LabelSpec) -> bytes:
        """Render ``labels`` (respecting ``spec.copies``) and return raw bytes."""
        raise NotImplementedError
