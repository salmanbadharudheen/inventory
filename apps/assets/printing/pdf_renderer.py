"""PDF label renderer (ReportLab).

Renders one asset label per PDF page at the exact physical sticker size.
Both QR and Code128 are drawn directly as vector graphics so the generated PDF
stays sharp when printed at actual size on thermal 2x1 labels.
"""

from __future__ import annotations

import io

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from .base import LabelRenderer, LabelData, LabelSpec


FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_MONO = 'Courier-Bold'


class PDFLabelRenderer(LabelRenderer):
    """Render labels to a multi-page, exact-size vector PDF."""

    content_type = 'application/pdf'
    file_extension = 'pdf'
    mode = 'pdf'

    def render(self, labels: list[LabelData], spec: LabelSpec) -> bytes:
        buffer = io.BytesIO()
        page_w = spec.width_mm * mm
        page_h = spec.height_mm * mm

        c = canvas.Canvas(buffer, pagesize=(page_w, page_h))
        c.setTitle('Asset Labels')

        # Tell PDF viewers (Chrome/Adobe) to print at the exact page size and
        # NOT scale to fit the destination paper. This is what makes the label
        # land precisely on the sticker without the user toggling "Actual size".
        try:
            c.setViewerPreference('PrintScaling', 'None')
            c.setViewerPreference('FitWindow', 'true')
        except Exception:
            pass

        for data in labels:
            for _ in range(spec.copies):
                self._draw_label(c, data, spec, page_w, page_h)
                c.showPage()

        c.save()
        return buffer.getvalue()

    # ── Layout ────────────────────────────────────────────────────────────
    def _draw_label(self, c, data: LabelData, spec: LabelSpec, W: float, H: float) -> None:
        margin = 0.8 * mm
        tag = data.safe_tag()
        if not tag:
            return

        # Thin sticker frame.
        c.setLineWidth(0.3)
        c.rect(0.25 * mm, 0.25 * mm, W - 0.5 * mm, H - 0.5 * mm, stroke=1, fill=0)

        design = (spec.design or 'CLASSIC').upper()
        # Show header only on labels tall enough to spare the space.
        has_room_for_header = (H >= 22 * mm) and spec.show_org and bool(data.org_name)

        # Header (org name, optional small logo)
        top = H - margin
        if has_room_for_header:
            header_h = self._draw_header(c, data, W, H, margin)
            top -= header_h

        content_top = top
        content_bottom = margin
        content_h = max(0.0, content_top - content_bottom)
        content_w = W - 2 * margin

        if design == 'QR_ONLY' or (spec.show_qr and not spec.show_barcode):
            self._draw_centered_qr(c, tag, margin, content_bottom, content_w, content_h)
            return
        if design == 'BARCODE_ONLY' or (spec.show_barcode and not spec.show_qr):
            self._draw_centered_barcode(c, tag, margin, content_bottom, content_w, content_h)
            return

        # Default CLASSIC-style: QR left, barcode + tag right.
        self._draw_qr_and_barcode(c, data, spec, margin, content_bottom, content_w, content_h)

    def _draw_header(self, c, data: LabelData, W: float, H: float, margin: float) -> float:
        header_h = 4.2 * mm
        header_bottom = H - margin - header_h
        baseline = header_bottom + 1.5 * mm
        text = data.org_name.strip()
        font_size = self._fit_font(c, text, FONT_BOLD, W - 2 * margin, 4.6, 2.8)

        logo_drawn = 0.0
        if data.logo_path:
            logo_h = header_h - 0.4 * mm
            logo_y = header_bottom + (header_h - logo_h) / 2.0
            logo_drawn = self._try_draw_logo(c, data.logo_path, margin, logo_y, logo_h)

        c.setFont(FONT_BOLD, font_size)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(W / 2.0, baseline, text)
        return header_h

    def _draw_qr_and_barcode(self, c, data: LabelData, spec: LabelSpec,
                             x: float, y: float, w: float, h: float) -> None:
        tag = data.safe_tag()
        qr_col_w = w * 0.22
        barcode_col_w = w * 0.78
        gap = 0.7 * mm
        qr_box_w = max(0.0, qr_col_w - gap / 2.0)
        barcode_box_w = max(0.0, barcode_col_w - gap / 2.0)
        barcode_x = x + qr_col_w + gap / 2.0

        if not self._barcode_fits_width(tag, barcode_box_w, 0.20):
            self._draw_stacked_qr_and_barcode(c, tag, x, y, w, h)
            return

        tag_font = self._fit_font(c, tag, FONT_MONO, barcode_box_w, 2.4, 1.8)
        tag_h = tag_font

        qr_side = min(qr_box_w, h * 0.76)
        qr_x = x + (qr_box_w - qr_side) / 2.0
        qr_y = y + (h - qr_side) / 2.0
        self._draw_qr(c, tag, qr_x, qr_y, qr_side)

        # Reserve a clear quiet-zone and keep a practical thermal bar height.
        bar_h = min(10.5 * mm, max(8.5 * mm, h - tag_h - 0.35 * mm))
        block_h = bar_h + 0.2 * mm + tag_h
        block_y = y + (h - block_h) / 2.0
        bar_y = block_y + tag_h + 0.2 * mm
        self._draw_barcode_fitted(c, tag, barcode_x, bar_y, barcode_box_w, bar_h)

        c.setFont(FONT_MONO, tag_font)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(barcode_x + barcode_box_w / 2.0, block_y, tag)

    def _draw_stacked_qr_and_barcode(self, c, tag: str, x: float, y: float, w: float, h: float) -> None:
        """Fallback layout: tiny QR, full-width barcode for long asset tags."""
        tag_font = self._fit_font(c, tag, FONT_MONO, w, 2.2, 1.7)
        tag_h = tag_font

        qr_side = min(5.5 * mm, w * 0.14, h * 0.28)
        bar_h = min(10.8 * mm, max(8.8 * mm, h - tag_h - qr_side - 0.6 * mm))
        block_h = qr_side + 0.25 * mm + bar_h + 0.2 * mm + tag_h
        block_y = y + (h - block_h) / 2.0

        bar_x = x
        bar_y = block_y + tag_h + 0.2 * mm
        self._draw_barcode_fitted(c, tag, bar_x, bar_y, w, bar_h)

        qr_x = x + (w - qr_side) / 2.0
        qr_y = bar_y + bar_h + 0.25 * mm
        self._draw_qr(c, tag, qr_x, qr_y, qr_side)

        c.setFont(FONT_MONO, tag_font)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + w / 2.0, block_y, tag)

    def _draw_centered_qr(self, c, tag: str, x: float, y: float, w: float, h: float) -> None:
        tag_font = self._fit_font(c, tag, FONT_MONO, w, 5.0, 2.6)
        tag_h = tag_font * 1.05
        qr_side = min(h - tag_h - 0.15 * mm, w)
        qr_side = max(qr_side, 4 * mm)
        self._draw_qr(c, tag, x + (w - qr_side) / 2.0, y + tag_h + 0.15 * mm, qr_side)
        c.setFont(FONT_MONO, tag_font)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + w / 2.0, y + 0.3 * mm, tag)

    def _draw_centered_barcode(self, c, tag: str, x: float, y: float, w: float, h: float) -> None:
        tag_font = self._fit_font(c, tag, FONT_MONO, w, 5.0, 2.6)
        tag_h = tag_font * 1.05
        bar_h = max(5.5 * mm, h - tag_h - 0.15 * mm)
        self._draw_barcode_fitted(c, tag, x, y + tag_h + 0.15 * mm, w, bar_h)
        c.setFont(FONT_MONO, tag_font)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + w / 2.0, y + 0.3 * mm, tag)

    # ── Primitives ────────────────────────────────────────────────────────
    def _draw_barcode_fitted(self, c, value: str, x: float, y: float,
                             max_w: float, bar_h: float) -> float:
        """Draw a vector Code128 barcode without raster conversion.

        We intentionally keep a minimum practical thermal module width and only
        fit the symbol inside the available barcode column. This avoids browser
        or PDF-layer bitmap scaling and preserves crisp vector bar edges.
        """
        target_w_mm = max_w / mm
        # A practical module width for 203 DPI thermal printing is ~0.20-0.24mm.
        preferred_bar_widths_mm = (0.24, 0.22, 0.20, 0.18)

        chosen = None
        for bar_width_mm in preferred_bar_widths_mm:
            bc = code128.Code128(
                value,
                barHeight=bar_h,
                barWidth=bar_width_mm * mm,
                humanReadable=False,
                quiet=1,
            )
            if (bc.width / mm) <= target_w_mm:
                chosen = bc
                break

        if chosen is None:
            # Last-resort fit: compute the largest vector module width that fits.
            probe = code128.Code128(value, barHeight=bar_h, barWidth=0.18 * mm, humanReadable=False, quiet=1)
            if not probe.width:
                return 0.0
            scale = max_w / probe.width
            chosen = code128.Code128(
                value,
                barHeight=bar_h,
                barWidth=0.18 * mm * scale,
                humanReadable=False,
                quiet=1,
            )

        draw_x = x + (max_w - chosen.width) / 2.0
        chosen.drawOn(c, draw_x, y)
        return chosen.width

    def _barcode_fits_width(self, value: str, available_w: float, module_width_mm: float) -> bool:
        barcode = code128.Code128(
            value,
            barHeight=8 * mm,
            barWidth=module_width_mm * mm,
            humanReadable=False,
            quiet=1,
        )
        return barcode.width <= available_w

    def _draw_qr(self, c, value: str, x: float, y: float, size: float) -> None:
        """Draw a QR code as vector graphics scaled to ``size`` x ``size``."""
        widget = qr.QrCodeWidget(value, barLevel='M')
        bounds = widget.getBounds()
        bw = bounds[2] - bounds[0]
        bh = bounds[3] - bounds[1]
        if not bw or not bh:
            return
        drawing = Drawing(size, size, transform=[size / bw, 0, 0, size / bh, 0, 0])
        drawing.add(widget)
        renderPDF.draw(drawing, c, x, y)

    def _try_draw_logo(self, c, logo_path: str, x: float, y: float, max_h: float) -> float:
        """Best-effort embed of the org logo; returns drawn width (0 on failure)."""
        try:
            from django.core.files.storage import default_storage
            if not logo_path or not default_storage.exists(logo_path):
                return 0.0
            with default_storage.open(logo_path, 'rb') as fh:
                reader = ImageReader(io.BytesIO(fh.read()))
            iw, ih = reader.getSize()
            if not iw or not ih:
                return 0.0
            draw_w = max_h * (iw / ih)
            c.drawImage(reader, x, y, width=draw_w, height=max_h,
                        preserveAspectRatio=True, mask='auto')
            return draw_w
        except Exception:
            return 0.0

    def _fit_font(self, c, text: str, font: str, max_w: float,
                  start: float, min_size: float) -> float:
        if not text:
            return start
        size = start
        while size > min_size and c.stringWidth(text, font, size) > max_w:
            size -= 0.5
        return size
