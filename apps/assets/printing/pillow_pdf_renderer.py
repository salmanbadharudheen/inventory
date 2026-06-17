"""Pillow-based PDF label fallback.

This renderer keeps the PDF endpoint usable when WeasyPrint and ReportLab are
not installed. It renders exact-size raster pages at the requested DPI and lets
Pillow write them as a multi-page PDF.
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw

from .base import LabelData, LabelRenderer, LabelSpec
from ..code_generators import AssetCodeGenerator


MM_PER_INCH = 25.4


class PillowPDFLabelRenderer(LabelRenderer):
    """Render labels to an exact-size raster PDF using Pillow only."""

    content_type = 'application/pdf'
    file_extension = 'pdf'
    mode = 'pdf'
    disposition = 'inline'

    def render(self, labels: list[LabelData], spec: LabelSpec) -> bytes:
        pages = []
        dpi = max(int(spec.dpi or 300), 300)
        width_px = max(1, round(spec.width_mm / MM_PER_INCH * dpi))
        height_px = max(1, round(spec.height_mm / MM_PER_INCH * dpi))

        for label in labels:
            for _ in range(spec.copies):
                pages.append(self._draw_label(label, spec, width_px, height_px, dpi))

        if not pages:
            raise NotImplementedError('No labels were available to render.')

        buffer = io.BytesIO()
        first, rest = pages[0], pages[1:]
        first.save(
            buffer,
            format='PDF',
            resolution=dpi,
            save_all=True,
            append_images=rest,
        )
        return buffer.getvalue()

    def _draw_label(self, label: LabelData, spec: LabelSpec, width: int, height: int, dpi: int) -> Image.Image:
        page = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(page)
        tag = label.safe_tag()

        margin = max(round(dpi * 0.035), 8)
        draw.rectangle((1, 1, width - 2, height - 2), outline='black', width=max(1, dpi // 300))

        if not tag:
            return page

        content_x = margin
        content_y = margin
        content_w = width - (margin * 2)
        content_h = height - (margin * 2)

        show_qr = spec.design == 'QR_ONLY' or (spec.show_qr and spec.design != 'BARCODE_ONLY')
        show_barcode = spec.design == 'BARCODE_ONLY' or (spec.show_barcode and spec.design != 'QR_ONLY')

        if show_barcode and not show_qr:
            self._paste_barcode(page, tag, content_x, content_y, content_w, content_h, dpi)
            return page
        if show_qr and not show_barcode:
            self._paste_qr(page, tag, content_x, content_y, content_w, content_h, dpi)
            return page

        qr_side = min(round(content_h * 0.72), round(content_w * 0.18))
        gap = max(round(dpi * 0.015), 4)
        qr_x = content_x + max((round(content_w * 0.20) - qr_side) // 2, 0)
        qr_y = content_y + (content_h - qr_side) // 2
        self._paste_qr(page, tag, qr_x, qr_y, qr_side, qr_side, dpi)

        barcode_x = content_x + round(content_w * 0.20) + gap
        barcode_w = width - margin - barcode_x
        self._paste_barcode(page, tag, barcode_x, content_y, barcode_w, content_h, dpi)
        return page

    def _paste_barcode(self, page: Image.Image, tag: str, x: int, y: int, w: int, h: int, dpi: int) -> None:
        barcode_img = AssetCodeGenerator.generate_barcode(tag, dpi=dpi).convert('RGB')
        barcode_img = self._trim_white(barcode_img)

        target_w = max(1, round(w * 0.94))
        target_h = max(1, round(h * 0.72))
        fitted = self._fit(barcode_img, target_w, target_h)
        paste_x = x + (w - fitted.width) // 2
        paste_y = y + (h - fitted.height) // 2
        page.paste(fitted, (paste_x, paste_y))

    def _paste_qr(self, page: Image.Image, tag: str, x: int, y: int, w: int, h: int, dpi: int) -> None:
        qr_img = AssetCodeGenerator.generate_qr_code(tag, dpi=dpi).convert('RGB')
        side = max(1, min(w, h))
        qr_img = qr_img.resize((side, side), Image.Resampling.NEAREST)
        page.paste(qr_img, (x + (w - side) // 2, y + (h - side) // 2))

    def _fit(self, image: Image.Image, max_w: int, max_h: int) -> Image.Image:
        scale = min(max_w / image.width, max_h / image.height)
        size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        return image.resize(size, Image.Resampling.NEAREST)

    def _trim_white(self, image: Image.Image) -> Image.Image:
        mask = Image.new('RGB', image.size, 'white')
        diff = Image.eval(ImageChops.difference(image, mask), lambda p: 255 if p > 12 else 0)
        bbox = diff.getbbox()
        if not bbox:
            return image
        return image.crop(bbox)


try:
    from PIL import ImageChops
except Exception:  # pragma: no cover - Pillow is required before this renderer loads.
    ImageChops = None