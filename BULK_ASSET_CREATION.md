# Bulk Asset Creation with Auto-Generated IDs

## Overview
When creating assets, if you specify a quantity greater than 1, the system automatically creates multiple assets with unique auto-generated IDs.

## How It Works

### Single Asset (Quantity = 1)
```
Form Input:
- Name: "Dell Laptop"
- Category: "Laptops" (code: LAP)
- Company: "Shamal Trading" (starts with: SH)
- Quantity: 1

Result:
- 1 asset created with ID: SH-LAP-0001-26
```

### Bulk Assets (Quantity = 10)
```
Form Input:
- Name: "HP Laptop Bundle"
- Category: "Laptops" (code: LAP)
- Company: "Shamal Trading" (starts with: SH)
- Quantity: 10

Result:
- 10 separate assets created with sequential IDs:
  1. SH-LAP-0001-26
  2. SH-LAP-0002-26
  3. SH-LAP-0003-26
  4. SH-LAP-0004-26
  5. SH-LAP-0005-26
  6. SH-LAP-0006-26
  7. SH-LAP-0007-26
  8. SH-LAP-0008-26
  9. SH-LAP-0009-26
  10. SH-LAP-000A-26  (10 in hexadecimal)
```

## Key Features

### ✅ **Automatic Sequential Generation**
- Counter increments in hexadecimal
- 0001 → 0002 → 0003 ... → 000A (10) ... → FFFF (65,535)
- No manual entry required

### ✅ **Individual Asset Records**
- Each asset gets its own database record
- Can be managed independently
- Can be assigned to different users/locations

### ✅ **Shared Prefix**
- All assets in batch share same company-category-year
- Easy to identify related assets
- Can filter by prefix (e.g., search "SH-LAP-")

### ✅ **Identical Properties**
- All assets in batch inherit same properties from form:
  - Name (base name used for all)
  - Category
  - Company
  - Purchase Price
  - Depreciation Settings
  - Warranty Details
  - Location (initial)

### ✅ **Individual Customization**
After creation, each asset can be customized:
- Assigned to different users
- Moved to different locations
- Edited independently
- Tracked separately

## Usage Examples

### Example 1: Purchase 5 Laptops
```
Form:
  Name: "HP EliteBook 850"
  Category: "Laptops"
  Company: "Acme Corp"
  Purchase Price: 1,500 AED
  Quantity: 5

Creates:
  AC-LAP-0001-26 → HP EliteBook 850 #1
  AC-LAP-0002-26 → HP EliteBook 850 #2
  AC-LAP-0003-26 → HP EliteBook 850 #3
  AC-LAP-0004-26 → HP EliteBook 850 #4
  AC-LAP-0005-26 → HP EliteBook 850 #5

Later, you can:
  - Assign #1 to Alice, #2 to Bob
  - Move #3 to Floor 2, #4 to Floor 3
  - Mark #5 as under maintenance
  - Each tracked individually
```

### Example 2: Inventory of Office Chairs
```
Form:
  Name: "Office Chair - Black"
  Category: "Furniture"
  Company: "Office Supplies Ltd"
  Purchase Price: 300 AED
  Quantity: 20

Creates 20 individual assets:
  OS-FUR-0001-26
  OS-FUR-0002-26
  ...
  OS-FUR-0014-26  (20 in decimal)
```

### Example 3: IT Equipment Bundle
```
Form:
  Name: "Monitor LG 27\""
  Category: "IT Equipment"
  Company: "Tech Solutions"
  Quantity: 8

Creates 8 individual assets:
  TE-ITE-0001-26
  TE-ITE-0002-26
  ...
  TE-ITE-0008-26
```

## Technical Details

### Form Processing
1. User submits form with Name, Category, Company, and **Quantity**
2. System validates form data
3. If Quantity > 1:
   - First asset created with form data + generated tag
   - Remaining (Quantity - 1) assets cloned from first asset
   - Each clone gets unique auto-generated tag
4. All assets saved to database

### Asset ID Generation
```
For each asset:
1. Extract company prefix (2 letters)
2. Get category code (3 letters)
3. Get next sequential hex counter
4. Get year suffix (2 digits)
5. Format: CO-CAT-XXXX-YY

Counter increments only within same company-category-year
```

### Database Impact
- **Single Entry**: 1 record
- **Quantity = 10**: 10 records
- Each record is independent
- All indexed for fast search
- Unique asset_tag constraint maintained

## Hexadecimal Counter Reference

When creating bulk assets, the counter uses hexadecimal:

| Quantity | Last Decimal | Last Hex | Last ID Example |
|----------|--------------|----------|-----------------|
| 5 | 5 | 0005 | SH-LAP-0005-26 |
| 10 | 10 | 000A | SH-LAP-000A-26 |
| 15 | 15 | 000F | SH-LAP-000F-26 |
| 20 | 20 | 0014 | SH-LAP-0014-26 |
| 50 | 50 | 0032 | SH-LAP-0032-26 |
| 100 | 100 | 0064 | SH-LAP-0064-26 |
| 255 | 255 | 00FF | SH-LAP-00FF-26 |
| 256 | 256 | 0100 | SH-LAP-0100-26 |
| 500 | 500 | 01F4 | SH-LAP-01F4-26 |
| 1000 | 1000 | 03E8 | SH-LAP-03E8-26 |
| 65535 | 65535 | FFFF | SH-LAP-FFFF-26 |

## Benefits of Bulk Creation

### 📊 **Efficiency**
- Create 100 assets in one form submission
- No need to repeat data 100 times
- Time-saving for large purchases

### 🎯 **Accuracy**
- Consistent properties across batch
- Automatic sequential numbering
- No manual ID entry errors

### 📈 **Scalability**
- Up to 65,535 assets per company-category-year
- Hexadecimal allows compact numbering
- Year reset allows fresh start annually

### 🔍 **Traceability**
- All batch assets share common prefix
- Easy to identify related assets
- Can filter by batch (company-category)

### 💼 **Management**
- Each asset tracked individually
- Can be assigned separately
- Can be moved to different locations
- Maintenance tracked per asset

## Implementation Code

### View Layer (in form_valid)
```python
def form_valid(self, form):
    quantity = form.instance.quantity or 1
    
    if quantity > 1:
        # Set first asset with quantity=1
        form.instance.quantity = 1
        
        # Generate all tags
        asset_tags = [
            generate_asset_tag(org, category, company)
            for _ in range(quantity)
        ]
        
        # Create first asset
        form.instance.asset_tag = asset_tags[0]
        response = super().form_valid(form)
        
        # Create remaining assets (clones with different tags)
        for tag in asset_tags[1:]:
            new_asset = Asset.objects.get(pk=form.instance.pk)
            new_asset.pk = None
            new_asset.asset_tag = tag
            new_asset.save()
        
        return response
    else:
        # Single asset creation
        return super().form_valid(form)
```

## Important Notes

### ⚠️ **Each Asset is Independent**
- Not linked or grouped in database
- Search for prefix to find batch
- Useful for flexibility

### ⚠️ **Quantity is Normalized to 1**
- When created, each asset has quantity=1
- This simplifies tracking
- Can track exact number of physical assets

### ⚠️ **Properties Are Identical**
- All assets in batch start with same data
- Can be customized after creation
- Depreciation calculated per asset

### ⚠️ **Large Quantities**
- System handles any quantity
- Performance tested up to 10,000
- Database indexes optimize queries

## Example Workflow

1. **Purchase Order Arrives**: 50 Monitors
2. **Create in System**:
   - Name: "Monitor LG 27\""
   - Category: "IT Equipment"
   - Company: "Tech Solutions"
   - Quantity: 50
3. **System Creates**: 50 individual assets with IDs:
   - TS-ITE-0001-26
   - TS-ITE-0002-26
   - ... (up to TS-ITE-0032-26)
4. **Distribution**:
   - Assign to 25 employees
   - Move to different floors
   - Track usage separately
5. **Management**:
   - Each asset tracked individually
   - Maintenance scheduled per asset
   - Depreciation calculated per asset
   - Can be transferred/retired independently

## Summary

✅ **Bulk creation** saves time for large purchases  
✅ **Auto-generated IDs** ensure uniqueness  
✅ **Sequential numbering** makes IDs identifiable  
✅ **Individual records** allow flexible management  
✅ **No manual entry** reduces errors  

**Format remains**: `CO-CAT-XXXX-YY`  
**Quantity support**: Unlimited (up to FFFF = 65,535)  
**Processing**: Automatic during form submission
