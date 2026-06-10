"""Vector PDF label renderer (ReportLab).

Renders one asset label per PDF page at the exact physical sticker size.
Barcodes (Code128) and QR codes are drawn as native vector graphics, so the
output stays razor-sharp at any printer resolution and prints dark and
consistent on thermal / sticker printers — no browser scaling, no rasterising.
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

        for data in labels:
            for _ in range(spec.copies):
                self._draw_label(c, data, spec, page_w, page_h)
                c.showPage()

        c.save()
        return buffer.getvalue()

    # ── Layout ────────────────────────────────────────────────────────────
    def _draw_label(self, c, data: LabelData, spec: LabelSpec, W: float, H: float) -> None:
        margin = 1.0 * mm
        tag = data.safe_tag()
        if not tag:
            return

        # Thin sticker frame for visual parity with the on-screen label.
        c.setLineWidth(0.4)
        c.rect(0.4 * mm, 0.4 * mm, W - 0.8 * mm, H - 0.8 * mm, stroke=1, fill=0)

        design = (spec.design or 'CLASSIC').upper()
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
        header_h = 3.6 * mm
        baseline = H - margin - header_h + 0.9 * mm
        text = data.org_name.strip()
        font_size = self._fit_font(c, text, FONT_BOLD, W - 2 * margin - 6 * mm, 8.0, 5.0)

        logo_drawn = 0.0
        if data.logo_path:
            logo_drawn = self._try_draw_logo(c, data.logo_path, margin, baseline - 0.6 * mm, header_h - 1.0 * mm)

        c.setFont(FONT_BOLD, font_size)
        c.setFillColorRGB(0, 0, 0)
        if logo_drawn:
            c.drawString(margin + logo_drawn + 1.2 * mm, baseline, text)
        else:
            c.drawCentredString(W / 2.0, baseline, text)
        return header_h

    def _draw_qr_and_barcode(self, c, data: LabelData, spec: LabelSpec,
                             x: float, y: float, w: float, h: float) -> None:
        gap = 1.4 * mm
        qr_side = min(h, w * 0.40)
        qr_x = x
        qr_y = y + (h - qr_side) / 2.0
        self._draw_qr(c, data.safe_tag(), qr_x, qr_y, qr_side)

        right_x = qr_x + qr_side + gap
        right_w = max(0.0, (x + w) - right_x)

        tag = data.safe_tag()
        tag_font = self._fit_font(c, tag, FONT_MONO, right_w, 7.0, 4.0)
        tag_h = tag_font * 1.1
        bar_h = max(4 * mm, h - tag_h - 1.0 * mm)

        # Barcode occupies the top of the right column.
        bar_y = y + tag_h + 0.6 * mm
        self._draw_barcode_fitted(c, tag, right_x, bar_y, right_w, bar_h)

        # Human-readable tag centred under the barcode.
        c.setFont(FONT_MONO, tag_font)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(right_x + right_w / 2.0, y + 0.4 * mm, tag)

    def _draw_centered_qr(self, c, tag: str, x: float, y: float, w: float, h: float) -> None:
        tag_font = self._fit_font(c, tag, FONT_MONO, w, 8.0, 4.0)
        tag_h = tag_font * 1.15
        qr_side = min(h - tag_h - 0.6 * mm, w)
        qr_side = max(qr_side, 4 * mm)
        self._draw_qr(c, tag, x + (w - qr_side) / 2.0, y + tag_h + 0.4 * mm, qr_side)
        c.setFont(FONT_MONO, tag_font)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + w / 2.0, y + 0.3 * mm, tag)

    def _draw_centered_barcode(self, c, tag: str, x: float, y: float, w: float, h: float) -> None:
        tag_font = self._fit_font(c, tag, FONT_MONO, w, 8.0, 4.0)
        tag_h = tag_font * 1.15
        bar_h = max(4 * mm, h - tag_h - 0.6 * mm)
        self._draw_barcode_fitted(c, tag, x, y + tag_h + 0.4 * mm, w, bar_h)
        c.setFont(FONT_MONO, tag_font)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + w / 2.0, y + 0.3 * mm, tag)

    # ── Primitives ────────────────────────────────────────────────────────
    def _draw_barcode_fitted(self, c, value: str, x: float, y: float,
                             max_w: float, bar_h: float) -> float:
        """Draw a Code128 barcode fitted within ``max_w`` (vector)."""
        base_bw = 0.5
        bc = code128.Code128(value, barHeight=bar_h, barWidth=base_bw, humanReadable=False)
        if not bc.width:
            return 0.0
        scaled_bw = base_bw * (max_w / bc.width)
        bc = code128.Code128(value, barHeight=bar_h, barWidth=scaled_bw, humanReadable=False)
        draw_x = x + (max_w - bc.width) / 2.0
        bc.drawOn(c, draw_x, y)
        return bc.width

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
