from __future__ import annotations

from typing import Iterable
from django.template.loader import render_to_string
from django.conf import settings

try:
    from weasyprint import HTML, CSS
except Exception:
    HTML = None

from .base import LabelData, LabelSpec


class WeasyLabelRenderer:
    """Render labels to PDF using WeasyPrint (server-side HTML → PDF).

    Produces higher-quality PDFs with better SVG handling than some client flows.
    """
    file_extension = 'pdf'
    content_type = 'application/pdf'
    disposition = 'inline'

    def render(self, labels: Iterable[LabelData], spec: LabelSpec) -> bytes:
        if HTML is None:
            raise NotImplementedError('WeasyPrint is not available in this environment.')

        context = {
            'assets': labels,
            'labels': labels,
            'spec': spec,
            'design': spec.design,
            'org': None,
        }

        # Render the same template used for browser printing, but with server-side
        # context so embedded SVGs (barcode/QR) can be inlined.
        html = render_to_string('assets/print_label.html', context)

        # Use default CSS from settings if present, else rely on embedded styles
        css_files = []
        try:
            wp_css = getattr(settings, 'WEASYPRINT_CSS', None)
            if wp_css:
                css_files = [CSS(filename=wp_css)]
        except Exception:
            css_files = []

        doc = HTML(string=html, base_url=settings.STATIC_ROOT or None)
        pdf = doc.write_pdf(stylesheets=css_files)
        return pdf
