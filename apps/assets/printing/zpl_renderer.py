"""Native Zebra ZPL II label renderer (optimised for the Zebra ZD220, 203 DPI).

ZPL describes every element in absolute printer dots, so the label prints at
EXACTLY the configured physical size — there is no browser/driver scaling, which
is the root cause of the "labels print too big" problem. This is the most
reliable path for the ZD220.

The generated ``.zpl`` can be sent to the printer via Zebra Setup Utilities,
copied to a shared/raw printer port, or streamed by Zebra Browser Print.
"""

from __future__ import annotations

from .base import LabelRenderer, LabelData, LabelSpec
from .barcode_utils import barcode_payload


def _dots(mm_value: float, dpi: int) -> int:
    """Convert millimetres to printer dots at the given DPI."""
    return int(round(mm_value * dpi / 25.4))


def _zpl_safe(text: str) -> str:
    """Strip ZPL control characters so data can't break the format."""
    if not text:
        return ''
    return (text.replace('^', ' ')
                .replace('~', ' ')
                .replace('\n', ' ')
                .replace('\r', ' ')
                .strip())


def _estimate_code128_modules(data: str) -> int:
    """Rough Code128 width in modules (start + data + checksum + stop + quiet)."""
    n = max(1, len(data))
    # ~11 modules per encoded char + 35 for start/checksum/stop, + quiet zones.
    return 11 * (n + 1) + 35


BARCODE_WIDTH_SCALE = 0.5


class ZPLLabelRenderer(LabelRenderer):
    """Render labels to native Zebra ZPL II (default 203 DPI for the ZD220)."""

    content_type = 'text/plain; charset=utf-8'
    file_extension = 'zpl'
    mode = 'zpl'
    disposition = 'attachment'  # download a .zpl file

    #: ZD220 is a 203 DPI printer.
    DEFAULT_DPI = 203

    def render(self, labels: list[LabelData], spec: LabelSpec) -> bytes:
        dpi = self.DEFAULT_DPI
        out: list[str] = []
        for data in labels:
            block = self._label_zpl(data, spec, dpi)
            if block:
                out.append(block)
        return ('\n'.join(out)).encode('utf-8')

    def _label_zpl(self, data: LabelData, spec: LabelSpec, dpi: int) -> str:
        tag = _zpl_safe(data.safe_tag())
        if not tag:
            return ''

        pw = _dots(spec.width_mm, dpi)      # print width (dots)
        ll = _dots(spec.height_mm, dpi)     # label length (dots)
        margin = _dots(2.0, dpi)            # 2 mm safe margin

        design = (spec.design or 'CLASSIC').upper()

        z: list[str] = []
        z.append('^XA')
        z.append('^CI28')                   # UTF-8 input encoding
        z.append(f'^PW{pw}')
        z.append(f'^LL{ll}')
        z.append('^LH0,0')
        z.append('^LT0')
        z.append('^MD30')                    # Maximum darkness for faded thermal labels.
        z.append('^PR2')                     # Slower print speed keeps bars darker/sharper.

        org = _zpl_safe(data.org_name)
        header_h = 0
        show_header = bool(org) and spec.show_org and ll >= _dots(20, dpi)
        if show_header:
            fh = _dots(2.6, dpi)            # ~2.6 mm tall org text
            header_h = fh + _dots(0.8, dpi)
            z.append(f'^FO0,{margin}^A0N,{fh},{fh}'
                     f'^FB{pw},1,0,C,0^FD{org}^FS')

        content_top = margin + header_h
        content_h = ll - content_top - margin

        if design == 'QR_ONLY' or (spec.show_qr and not spec.show_barcode):
            z.extend(self._centered_qr(tag, pw, content_top, content_h, margin, dpi))
        elif design == 'BARCODE_ONLY' or (spec.show_barcode and not spec.show_qr):
            z.extend(self._centered_barcode(tag, pw, content_top, content_h, margin, dpi))
        else:
            z.extend(self._qr_and_barcode(tag, pw, content_top, content_h, margin, dpi))

        if spec.copies and spec.copies > 1:
            z.append(f'^PQ{spec.copies},0,0,Y')
        z.append('^XZ')
        return '\n'.join(p for p in z if p)

    # ── Layouts ───────────────────────────────────────────────────────────
    def _qr_and_barcode(self, tag, pw, top, content_h, margin, dpi):
        z = []
        barcode_tag = barcode_payload(tag)
        # QR on the left, max ~8 mm.
        qr_target = min(_dots(8.0, dpi), content_h)
        qr_mag = max(2, min(6, int(round(qr_target / 25.0))))  # ~25 modules assumed
        qr_x = margin
        qr_y = top + max(0, (content_h - qr_target) // 2)
        z.append(f'^FO{qr_x},{qr_y}^BQN,2,{qr_mag}^FDMA,{tag}^FS')

        # Right column for the barcode + human-readable tag.
        gap = _dots(2.0, dpi)
        right_x = qr_x + qr_target + gap
        right_w = pw - right_x - margin
        if right_w < _dots(10, dpi):
            right_w = _dots(10, dpi)

        barcode_w = max(_dots(10, dpi), int(round(right_w * BARCODE_WIDTH_SCALE)))

        tag_h = _dots(2.4, dpi)
        bar_h = max(_dots(6.0, dpi), content_h - tag_h - _dots(1.0, dpi))

        modules = _estimate_code128_modules(tag)
        module_w = max(1, min(3, int(barcode_w / modules)))
        barcode_px_w = modules * module_w
        barcode_x = right_x + max(0, (right_w - barcode_px_w) // 2)
        z.append(f'^BY{module_w},2.4,{bar_h}')
        z.append(f'^FO{barcode_x},{top}^BCN,{bar_h},N,N,N^FD{barcode_tag}^FS')

        tag_y = top + bar_h + _dots(0.6, dpi)
        z.append(f'^FO{right_x},{tag_y}^A0N,{tag_h},{tag_h}'
                 f'^FB{right_w},1,0,C,0^FD{tag}^FS')
        return z

    def _centered_qr(self, tag, pw, top, content_h, margin, dpi):
        z = []
        tag_h = _dots(2.6, dpi)
        qr_target = min(content_h - tag_h - _dots(1.0, dpi), pw - 2 * margin)
        qr_target = max(qr_target, _dots(6.0, dpi))
        qr_mag = max(2, min(8, int(round(qr_target / 25.0))))
        qr_x = (pw - qr_target) // 2
        z.append(f'^FO{qr_x},{top}^BQN,2,{qr_mag}^FDMA,{tag}^FS')
        tag_y = top + qr_target + _dots(0.6, dpi)
        z.append(f'^FO0,{tag_y}^A0N,{tag_h},{tag_h}^FB{pw},1,0,C,0^FD{tag}^FS')
        return z

    def _centered_barcode(self, tag, pw, top, content_h, margin, dpi):
        z = []
        barcode_tag = barcode_payload(tag)
        tag_h = _dots(2.6, dpi)
        bar_h = max(_dots(8.0, dpi), content_h - tag_h - _dots(1.0, dpi))
        right_w = pw - 2 * margin
        barcode_w = max(_dots(10, dpi), int(round(right_w * BARCODE_WIDTH_SCALE)))
        modules = _estimate_code128_modules(barcode_tag)
        module_w = max(1, min(3, int(barcode_w / modules)))
        barcode_px_w = modules * module_w
        barcode_x = margin + max(0, (right_w - barcode_px_w) // 2)
        z.append(f'^BY{module_w},2.4,{bar_h}')
        z.append(f'^FO{barcode_x},{top}^BCN,{bar_h},N,N,N^FD{barcode_tag}^FS')
        tag_y = top + bar_h + _dots(0.6, dpi)
        z.append(f'^FO0,{tag_y}^A0N,{tag_h},{tag_h}^FB{pw},1,0,C,0^FD{tag}^FS')
        return z

