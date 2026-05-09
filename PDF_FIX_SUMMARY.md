# PDF Deployment Fix Summary

## Root Cause
The "Download PDF" feature used `xhtml2pdf` → which secretly depends on `svglib` → `pycairo` → **cairo C library** (a system-level library that Railway/Nixpacks doesn't have). This caused the entire Railway build to fail.

## What Was Fixed

1. **Replaced `xhtml2pdf` + `WeasyPrint`** (both need cairo) with **`fpdf2`** — pure Python, zero system dependencies.

2. **Rewrote the PDF view** (`AssetReconciliationReportPDFView`) to generate the reconciliation report directly with fpdf2:
   - KPI boxes (Total Assets, Original Cost, Acc. Depreciation, Net Book Value)
   - Tables broken down by Category, Status, Condition, Department, Site

3. **Cleaned up `requirements.txt`** — removed `xhtml2pdf`, `reportlab`, `svglib` and all related packages; added just `fpdf2==2.8.3`.

4. **Switched back to Nixpacks builder** — updated `railway.json` to `"builder": "NIXPACKS"`.

5. **Removed the Dockerfile** — no longer needed with Nixpacks.

## Key Lesson
`xhtml2pdf` and `WeasyPrint` both require the **cairo C library** at the OS level.  
Railway's Nixpacks environment does not provide it.  
Always use **`fpdf2`** for PDF generation on Railway — it is pure Python with no system dependencies.
