"""
Barcode and QR Code Generation Module for Assets
Handles creating, storing, and serving barcode/QR codes for asset identification.
"""

import io
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode
import barcode
from barcode.writer import ImageWriter
from django.core.files.base import ContentFile
from django.conf import settings


class AssetCodeGenerator:
    """Generates barcodes and QR codes for assets"""
    
    BARCODE_FORMAT = 'code128'  # Most common format
    QR_VERSION = 1  # Auto-detect size
    QR_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_M  # Medium error correction for small labels

    @staticmethod
    def _load_font(size, bold=False):
        """Load a usable font with graceful fallback across Windows/Linux."""
        font_candidates = []
        if bold:
            font_candidates = ["arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"]
        else:
            font_candidates = ["arial.ttf", "DejaVuSans.ttf", "Arial.ttf"]

        for font_name in font_candidates:
            try:
                return ImageFont.truetype(font_name, size)
            except (IOError, OSError):
                continue

        return ImageFont.load_default()

    @staticmethod
    def _fit_text(draw, text, max_width, start_size, bold=False, min_size=9):
        """Return the largest font that fits within the requested width."""
        if not text:
            return ImageFont.load_default()

        for size in range(start_size, min_size - 1, -1):
            font = AssetCodeGenerator._load_font(size, bold=bold)
            bbox = draw.textbbox((0, 0), text, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                return font

        return AssetCodeGenerator._load_font(min_size, bold=bold)
    
    @staticmethod
    def generate_barcode(asset_tag, dpi=72):
        """
        Generate a barcode image from asset tag.
        
        Args:
            asset_tag (str): Asset identification tag
            dpi (int): DPI for image quality (72=screen, 300=print)
        
        Returns:
            PIL.Image: Barcode image
        """
        try:
            # Create barcode using python-barcode
            barcode_instance = barcode.get(
                AssetCodeGenerator.BARCODE_FORMAT,
                asset_tag,
                writer=ImageWriter()
            )
            
            # Generate as image (very low DPI can break writer geometry)
            safe_dpi = max(int(dpi), 300)
            buffer = io.BytesIO()
            barcode_instance.write(buffer, {
                'dpi': safe_dpi,
                'module_width': 0.5,       # Wider bars for HD print quality
                'module_height': 15.0,     # Taller bars for reliable scanning
                'write_text': False,       # No text — tag shown separately in label
                'quiet_zone': 2.0,         # Proper quiet zone on sides
                'font_size': 0,            # Ensure no text even on fallback
            })
            buffer.seek(0)
            
            img = Image.open(buffer)
            # Keep reference to buffer to prevent garbage collection
            img._buffer = buffer
            return img.convert('RGB')
        except Exception as e:
            raise ValueError(f"Failed to generate barcode: {str(e)}")

    
    @staticmethod
    def generate_qr_code(asset_tag, dpi=72):
        """
        Generate a QR code image from asset tag.
        
        Args:
            asset_tag (str): Asset identification tag
            dpi (int): DPI for image quality (72=screen, 300=print)
        
        Returns:
            PIL.Image: QR code image
        """
        try:
            # Higher box_size for HD print quality, standard 4-module quiet zone
            box_size = 20 if dpi >= 300 else 14
            qr = qrcode.QRCode(
                version=AssetCodeGenerator.QR_VERSION,
                error_correction=AssetCodeGenerator.QR_ERROR_CORRECTION,
                box_size=box_size,
                border=4,  # Standard quiet zone for reliable scanning
            )
            qr.add_data(asset_tag)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            return img.convert('RGB')
        except Exception as e:
            raise ValueError(f"Failed to generate QR code: {str(e)}")
    
    @staticmethod
    def generate_label(asset_tag, company_name=None, include_text=True, width=260, height=150, dpi=72):
        """
        Generate a combined label with QR code, barcode, and text.
        Optimized for printing on labels.
        
        Args:
            asset_tag (str): Asset identification tag
            include_text (bool): Include text below codes
            width (int): Label width in pixels
            height (int): Label height in pixels
            dpi (int): DPI for image quality
        
        Returns:
            PIL.Image: Combined label image
        """
        try:
            company_name = (company_name or '').strip()

            # Generate source images
            qr_source = AssetCodeGenerator.generate_qr_code(asset_tag, dpi)
            barcode_source = AssetCodeGenerator.generate_barcode(asset_tag, dpi)

            # Create label base
            label = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(label)

            outer_border = '#d1d5db'
            accent = '#111827'
            muted = '#6b7280'
            card_bg = '#f8fafc'

            draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=10, outline=outer_border, width=1, fill='white')

            # Header area (company name)
            header_top = 8
            header_bottom = 20
            if company_name:
                company_font = AssetCodeGenerator._fit_text(draw, company_name, width - 24, start_size=16, bold=True, min_size=10)
                company_bbox = draw.textbbox((0, 0), company_name, font=company_font)
                company_w = company_bbox[2] - company_bbox[0]
                company_h = company_bbox[3] - company_bbox[1]
                company_y = header_top
                draw.text(((width - company_w) // 2, company_y), company_name, fill=accent, font=company_font)
                header_bottom = company_y + company_h + 6
                draw.line((14, header_bottom, width - 14, header_bottom), fill='#e5e7eb', width=1)

            # Content area
            content_top = header_bottom + 6
            content_bottom = height - 10
            content_height = max(content_bottom - content_top, 20)

            left_w = int(width * 0.40)
            gap = 8
            left_panel = (10, content_top, 10 + left_w, content_bottom)
            right_panel = (left_panel[2] + gap, content_top, width - 10, content_bottom)

            draw.rounded_rectangle(left_panel, radius=8, fill=card_bg, outline='#e5e7eb', width=1)
            draw.rounded_rectangle(right_panel, radius=8, fill=card_bg, outline='#e5e7eb', width=1)

            title_font = AssetCodeGenerator._load_font(9, bold=True)

            # Left panel: Asset ID above QR
            id_title = 'ASSET ID'
            id_title_bbox = draw.textbbox((0, 0), id_title, font=title_font)
            id_title_w = id_title_bbox[2] - id_title_bbox[0]
            id_title_h = id_title_bbox[3] - id_title_bbox[1]
            id_title_y = left_panel[1] + 6
            draw.text((left_panel[0] + ((left_panel[2] - left_panel[0] - id_title_w) // 2), id_title_y), id_title, fill=muted, font=title_font)

            id_font = AssetCodeGenerator._fit_text(draw, asset_tag, left_panel[2] - left_panel[0] - 12, start_size=11, bold=True, min_size=8)
            id_bbox = draw.textbbox((0, 0), asset_tag, font=id_font)
            id_w = id_bbox[2] - id_bbox[0]
            id_h = id_bbox[3] - id_bbox[1]
            id_y = id_title_y + id_title_h + 3
            draw.text((left_panel[0] + ((left_panel[2] - left_panel[0] - id_w) // 2), id_y), asset_tag, fill=accent, font=id_font)

            qr_available_h = left_panel[3] - (id_y + id_h) - 8
            qr_size = max(min(left_panel[2] - left_panel[0] - 14, qr_available_h), 36)
            qr_img = qr_source.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            qr_x = left_panel[0] + ((left_panel[2] - left_panel[0] - qr_size) // 2)
            qr_y = id_y + id_h + max((qr_available_h - qr_size) // 2, 2)
            label.paste(qr_img, (qr_x, qr_y))

            # Right panel: Barcode section
            barcode_title = 'BARCODE'
            barcode_title_bbox = draw.textbbox((0, 0), barcode_title, font=title_font)
            barcode_title_w = barcode_title_bbox[2] - barcode_title_bbox[0]
            barcode_title_h = barcode_title_bbox[3] - barcode_title_bbox[1]
            barcode_title_y = right_panel[1] + 6
            draw.text((right_panel[0] + ((right_panel[2] - right_panel[0] - barcode_title_w) // 2), barcode_title_y), barcode_title, fill=muted, font=title_font)

            barcode_area_w = right_panel[2] - right_panel[0] - 14
            barcode_area_h = right_panel[3] - barcode_title_y - barcode_title_h - 10
            barcode_text_h = 12 if include_text else 0
            barcode_h = max(min(42, barcode_area_h - barcode_text_h - 4), 20)
            barcode_w = max(min(barcode_area_w, int(barcode_h * 3.8)), 60)
            barcode_img = barcode_source.resize((barcode_w, barcode_h), Image.Resampling.LANCZOS)

            barcode_x = right_panel[0] + ((right_panel[2] - right_panel[0] - barcode_w) // 2)
            barcode_y = barcode_title_y + barcode_title_h + max((barcode_area_h - barcode_h - barcode_text_h) // 2, 2)
            label.paste(barcode_img, (barcode_x, barcode_y))

            if include_text:
                text_font = AssetCodeGenerator._fit_text(draw, asset_tag, barcode_area_w, start_size=10, bold=False, min_size=8)
                text_bbox = draw.textbbox((0, 0), asset_tag, font=text_font)
                text_w = text_bbox[2] - text_bbox[0]
                text_h = text_bbox[3] - text_bbox[1]
                text_x = right_panel[0] + ((right_panel[2] - right_panel[0] - text_w) // 2)
                text_y = min(barcode_y + barcode_h + 3, right_panel[3] - text_h - 2)
                draw.text((text_x, text_y), asset_tag, fill=accent, font=text_font)
            
            return label
        except Exception as e:
            raise ValueError(f"Failed to generate label: {str(e)}")
    
    @staticmethod
    def save_barcode_to_file(asset_tag, directory='assets/barcodes/'):
        """
        Save barcode image to file.
        
        Args:
            asset_tag (str): Asset identification tag
            directory (str): Directory path relative to MEDIA_ROOT
        
        Returns:
            str: File path relative to MEDIA_ROOT
        """
        try:
            img = AssetCodeGenerator.generate_barcode(asset_tag, dpi=300)
            
            # Create directory if needed
            media_dir = Path(settings.MEDIA_ROOT) / directory
            media_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{asset_tag}_barcode.png"
            filepath = media_dir / filename
            img.save(filepath, 'PNG')
            
            return f"{directory}{filename}"
        except Exception as e:
            print(f"Error saving barcode: {str(e)}")
            return None
    
    @staticmethod
    def save_qr_to_file(asset_tag, directory='assets/qr_codes/'):
        """
        Save QR code image to file.
        
        Args:
            asset_tag (str): Asset identification tag
            directory (str): Directory path relative to MEDIA_ROOT
        
        Returns:
            str: File path relative to MEDIA_ROOT
        """
        try:
            img = AssetCodeGenerator.generate_qr_code(asset_tag, dpi=300)
            
            # Create directory if needed
            media_dir = Path(settings.MEDIA_ROOT) / directory
            media_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{asset_tag}_qr.png"
            filepath = media_dir / filename
            img.save(filepath, 'PNG')
            
            return f"{directory}{filename}"
        except Exception as e:
            print(f"Error saving QR code: {str(e)}")
            return None
    
    @staticmethod
    def save_label_to_file(asset_tag, company_name=None, directory='assets/labels/'):
        """
        Save combined label to file.
        
        Args:
            asset_tag (str): Asset identification tag
            directory (str): Directory path relative to MEDIA_ROOT
        
        Returns:
            str: File path relative to MEDIA_ROOT
        """
        try:
            img = AssetCodeGenerator.generate_label(asset_tag, company_name=company_name, include_text=True, dpi=300)
            
            # Create directory if needed
            media_dir = Path(settings.MEDIA_ROOT) / directory
            media_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{asset_tag}_label.png"
            filepath = media_dir / filename
            img.save(filepath, 'PNG')
            
            return f"{directory}{filename}"
        except Exception as e:
            print(f"Error saving label: {str(e)}")
            return None


def generate_codes_for_asset(asset_instance):
    """
    Generate and save barcode/QR/label for an asset.
    Called automatically when asset is created.
    
    Args:
        asset_instance: Asset model instance
    """
    if not asset_instance.asset_tag:
        return
    
    try:
        barcode_path = AssetCodeGenerator.save_barcode_to_file(asset_instance.asset_tag)
        qr_path = AssetCodeGenerator.save_qr_to_file(asset_instance.asset_tag)
        company_name = None
        if getattr(asset_instance, 'company', None):
            company_name = asset_instance.company.name
        elif getattr(asset_instance, 'organization', None):
            company_name = getattr(asset_instance.organization, 'name', None)

        label_path = AssetCodeGenerator.save_label_to_file(asset_instance.asset_tag, company_name=company_name)
        
        # Update asset with code paths (if model has these fields)
        if hasattr(asset_instance, 'barcode_image') and barcode_path:
            asset_instance.barcode_image = barcode_path
        if hasattr(asset_instance, 'qr_code_image') and qr_path:
            asset_instance.qr_code_image = qr_path
        if hasattr(asset_instance, 'label_image') and label_path:
            asset_instance.label_image = label_path
        
        asset_instance.save(update_fields=['barcode_image', 'qr_code_image', 'label_image'])
    except Exception as e:
        print(f"Error generating codes for asset {asset_instance.asset_tag}: {str(e)}")
