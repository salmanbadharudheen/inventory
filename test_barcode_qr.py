#!/usr/bin/env python
"""
Test script for barcode/QR code generation
Run: python test_barcode_qr.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.code_generators import AssetCodeGenerator
from PIL import Image

def test_barcode_generation():
    """Test barcode generation"""
    print("Testing barcode generation...")
    try:
        test_tag = "TEST-0001-26"
        img = AssetCodeGenerator.generate_barcode(test_tag, dpi=600)
        assert img.size[0] >= 1200, f"Barcode width too small: {img.size}"
        assert img.size[1] >= 220, f"Barcode height too small: {img.size}"
        print(f"  ✓ Barcode generated: {img.size} {img.mode}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_qr_generation():
    """Test QR code generation"""
    print("Testing QR code generation...")
    try:
        test_tag = "TEST-0001-26"
        img = AssetCodeGenerator.generate_qr_code(test_tag, dpi=600)
        assert img.size[0] >= 900 and img.size[1] >= 900, f"QR size too small: {img.size}"
        print(f"  ✓ QR code generated: {img.size} {img.mode}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_label_generation():
    """Test label generation"""
    print("Testing label generation...")
    try:
        test_tag = "TEST-0001-26"
        img = AssetCodeGenerator.generate_label(test_tag, include_text=True, dpi=600)
        assert img.size == (1200, 600), f"Label size mismatch: {img.size}"
        print(f"  ✓ Label generated: {img.size} {img.mode}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_file_saving():
    """Test saving to files"""
    print("Testing file saving...")
    try:
        test_tag = "TEST-0001-26"
        barcode_path = AssetCodeGenerator.save_barcode_to_file(test_tag)
        qr_path = AssetCodeGenerator.save_qr_to_file(test_tag)
        label_path = AssetCodeGenerator.save_label_to_file(test_tag)
        
        if barcode_path and qr_path and label_path:
            print(f"  ✓ Barcode saved: {barcode_path}")
            print(f"  ✓ QR code saved: {qr_path}")
            print(f"  ✓ Label saved: {label_path}")
            return True
        else:
            print("  ✗ Some files were not saved")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Barcode & QR Code Generation Test Suite")
    print("=" * 60)
    
    results = []
    results.append(test_barcode_generation())
    results.append(test_qr_generation())
    results.append(test_label_generation())
    results.append(test_file_saving())
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if all(results):
        print("✓ All tests passed! Barcode/QR system is ready.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Check errors above.")
        sys.exit(1)
