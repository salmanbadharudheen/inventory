# QR Code & Barcode Generation System

## Overview

The system now automatically generates QR codes, barcodes, and combined labels for every asset created. These can be printed and attached to physical assets for identification and tracking.

## Features

✅ **Automatic Code Generation**
- QR codes auto-generated when asset is created
- Barcodes (Code128 format) for scanning
- Combined labels for printing on adhesive stickers

✅ **Download & Print**
- Individual download for QR, barcode, or label
- Batch download as ZIP for multiple assets
- High-resolution images (300 DPI) for printing

✅ **Integration**
- Codes encoded with `asset_tag` (unique system ID)
- Links to asset detail page when QR is scanned
- Accessible from asset detail view

✅ **Storage**
- Stored in organized media directories
- Organized by type: `/media/assets/barcodes/`, `/media/assets/qr_codes/`, `/media/assets/labels/`
- Non-editable fields (auto-managed)

## How to Use

### 1. Automatic Code Generation (On Asset Creation)
When you create a new asset, the system automatically:
1. Generates unique `asset_tag` (e.g., `ABC-0001-26`)
2. Creates barcode image
3. Creates QR code image
4. Creates combined printable label

### 2. View & Download Codes
1. Navigate to any asset detail page (`/assets/<id>/`)
2. Right sidebar shows the "Identification Codes" card
3. Options available:
   - **Download QR** - Get QR code PNG (PNG format, 300 DPI)
   - **Download Barcode** - Get barcode PNG (PNG format, 300 DPI)
   - **Print Label** - Download combined label for sticker printing

### 3. Regenerate Codes (If Needed)
- Click "Regenerate" button if codes get corrupted or lost
- System will recreate all three code types
- Useful if media files are accidentally deleted

### 4. Batch Download
For printing labels for multiple assets:
```
GET /assets/barcodes/download/batch/?asset_ids=<uuid1>,<uuid2>,<uuid3>
```
Returns a ZIP file containing all barcodes.

## Technical Details

### Code Formats

**Barcode Format:** Code128
- Most widely supported format
- Can encode full asset_tag (e.g., ABC-0001-26)
- Print-ready at 300 DPI

**QR Code:**
- Version 1 (auto-detected if needed)
- Error correction level: L (7% recovery)
- Encodes: asset_tag (e.g., ABC-0001-26)
- When scanned, links to: `/assets/<asset_id>/` detail page

**Combined Label:**
- Includes QR code (80x80px)
- Includes barcode (200x40px)
- Includes text label (asset tag)
- Size: 200x100px (suitable for 2"x1" stickers at 200 DPI)
- Can be resized by printer for different label sizes

### File Locations

```
media/
├── assets/
│   ├── barcodes/
│   │   ├── ABC-0001-26_barcode.png
│   │   └── ABC-0002-26_barcode.png
│   ├── qr_codes/
│   │   ├── ABC-0001-26_qr.png
│   │   └── ABC-0002-26_qr.png
│   └── labels/
│       ├── ABC-0001-26_label.png
│       └── ABC-0002-26_label.png
```

### Database Fields (Asset Model)

```python
barcode_image = FileField()      # Path to barcode PNG (auto-managed)
qr_code_image = FileField()      # Path to QR code PNG (auto-managed)
label_image = FileField()        # Path to combined label PNG (auto-managed)
```

## API Endpoints

### Generate/Regenerate Codes
```
POST /assets/<uuid>/codes/generate/
```
Returns JSON with paths to all generated images.

### Download Individual Codes
```
GET /assets/<uuid>/barcode/download/
GET /assets/<uuid>/qr/download/
GET /assets/<uuid>/label/download/
```
Returns redirect to media file.

### Batch Download Barcodes
```
GET /assets/barcodes/download/batch/?asset_ids=<uuid>,<uuid>,<uuid>
```
Returns ZIP file.

## Installation & Dependencies

Required packages (already in requirements.txt):
- `Pillow` - Image processing
- `qrcode[pil]` - QR code generation
- `python-barcode` - Barcode generation

Install with:
```bash
pip install -r requirements.txt
```

## Production Considerations

1. **Image Storage:**
   - In production, serve media from S3/CloudFront (not Django app)
   - Set up appropriate caching headers
   - Use CDN for image delivery

2. **Performance:**
   - Code generation happens in save() hook (avoid blocking)
   - Consider moving to async task (Celery) for bulk operations
   - Image files are small (~5-20 KB each)

3. **Backup:**
   - Include `/media/assets/` in backup strategy
   - Images can be regenerated if lost (non-critical)

4. **Security:**
   - Media files inherit user organization scoping
   - QR code data is just the asset tag (no sensitive data)

## Troubleshooting

### Codes Not Generated
1. Check that `asset_tag` is set
2. Verify `/media/` directory is writable
3. Check Django logs for errors
4. Manually trigger regeneration from UI

### Print Quality Issues
1. Use 300 DPI images (saved automatically)
2. Test label size (200x100px = 1"x0.5" at 200 DPI, 2"x1" at 100 DPI)
3. Adjust printer settings for best results

### Missing Images in Media
1. Click "Regenerate" to restore lost codes
2. Check `MEDIA_ROOT` setting in Django
3. Verify file permissions on media directory

## Future Enhancements

- [ ] Bulk label generation as PDF (not just ZIP)
- [ ] Custom label design templates
- [ ] Barcode format options (QR, Code128, Code39, etc.)
- [ ] Async code generation for large batches
- [ ] Asset metadata in QR code (not just ID)
- [ ] Integration with label printing APIs
