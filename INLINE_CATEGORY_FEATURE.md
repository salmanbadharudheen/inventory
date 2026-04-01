# Inline Category & Subcategory Creation Feature

## Overview
Added the ability to create new categories and subcategories directly from the asset add/edit form without navigating away. This improves the user experience when filling out the form.

## Changes Made

### 1. Backend (views.py)
- Added `ajax_create_category()` function to handle inline category creation
- Added `ajax_create_subcategory()` function to handle inline subcategory creation
- Both functions include validation and duplicate checking

### 2. URLs (apps/assets/urls.py)
- Added route: `/assets/ajax/category/create/` → `ajax-create-category`
- Added route: `/assets/ajax/subcategory/create/` → `ajax-create-subcategory`

### 3. Template (templates/assets/asset_form.html)
- Added "+" buttons next to Category and Subcategory dropdown fields
- Added modal dialogs for creating new categories and subcategories
- Added JavaScript functions to handle modal open/close and form submission
- Added CSS styles for modals and inline add buttons

## How to Use

### Adding a Category:
1. Go to Assets → Add Asset (http://127.0.0.1:8000/assets/add/)
2. Click the "+" button next to the Category field
3. Fill in the category details:
   - Category Name (required)
   - Useful Life Years (default: 5)
   - Depreciation Method (default: Straight Line)
4. Click "Create Category"
5. The new category will be automatically selected in the dropdown

### Adding a Subcategory:
1. First select a Category from the dropdown
2. Click the "+" button next to the Subcategory field
3. Enter the subcategory name
4. Click "Create Subcategory"
5. The new subcategory will be automatically selected in the dropdown

## Features
- ✅ Real-time validation
- ✅ Duplicate name checking
- ✅ Automatic selection after creation
- ✅ No page refresh needed
- ✅ Clean modal interface
- ✅ Error handling with user-friendly messages
- ✅ Organization-scoped (only creates for user's organization)

## Technical Details
- Uses AJAX POST requests with CSRF protection
- Returns JSON responses with success/error status
- Automatically adds new options to select dropdowns
- Triggers change events to update dependent fields
