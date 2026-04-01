# Asset ID Auto-Generation System

## Overview
Asset IDs are now automatically generated using a structured format that makes them instantly identifiable and scalable.

## Format: `CO-CAT-XXXX-YY`

### Components

| Component | Description | Example | Generation |
|-----------|-------------|---------|------------|
| **CO** | Company Code (2 letters) | `SH`, `AC`, `MI` | Auto-extracted from company name |
| **CAT** | Category Code (3 letters) | `LAP`, `FUR`, `ITE` | Already auto-generated in system |
| **XXXX** | Hexadecimal Counter (4 digits) | `0001`, `001A`, `00FF` | Sequential per company-category-year |
| **YY** | Year Suffix (2 digits) | `26`, `27`, `28` | Current year (last 2 digits) |

## Real-World Examples

```
SH-LAP-0001-26  →  Shamal Trading, Laptop, 1st asset, Year 2026
SH-LAP-001A-26  →  Shamal Trading, Laptop, 26th asset, Year 2026
AC-FUR-00FF-26  →  Acme Corp, Furniture, 255th asset, Year 2026
MI-ITE-1234-26  →  Microsoft, IT Equipment, 4660th asset, Year 2026
AP-VEH-FFFF-25  →  Apple Inc, Vehicles, 65,535th asset, Year 2025
```

## Key Features

### ✅ **Instantly Identifiable**
- See company and category at a glance
- Year suffix shows when asset was registered
- No need to look up database

### ✅ **Highly Scalable**
- **65,535 assets** per company-category-year combination
- Automatic counter reset each year
- Hexadecimal format maximizes 4-digit space

### ✅ **Automatic Generation**
1. **Company Code**: Auto-extracted when company is created
   - "Shamal Trading" → `SH`
   - "Microsoft" → `MI`
   - "XY Company" → `XY`

2. **Category Code**: Already exists in system (3 letters)
   - "Laptop Computers" → `LAP001`
   - "Furniture" → `FUR001`

3. **Counter**: Increments automatically for each new asset
   - Starts at `0001` each year
   - Counts in hexadecimal: 0001, 0002... 000A... 00FF... FFFF

4. **Year**: Current year automatically appended

### ✅ **Year Rollover**
Counters reset each January 1st:
```
2025-12-31: SH-LAP-0FFF-25  (Last asset of 2025)
2026-01-01: SH-LAP-0001-26  (First asset of 2026)
```

## Hexadecimal Counter Reference

| Decimal | Hex | Asset ID Example |
|---------|-----|------------------|
| 1 | 0001 | SH-LAP-0001-26 |
| 10 | 000A | SH-LAP-000A-26 |
| 26 | 001A | SH-LAP-001A-26 |
| 100 | 0064 | SH-LAP-0064-26 |
| 255 | 00FF | SH-LAP-00FF-26 |
| 256 | 0100 | SH-LAP-0100-26 |
| 1,000 | 03E8 | SH-LAP-03E8-26 |
| 4,095 | 0FFF | SH-LAP-0FFF-26 |
| 4,096 | 1000 | SH-LAP-1000-26 |
| 10,000 | 2710 | SH-LAP-2710-26 |
| 65,535 | FFFF | SH-LAP-FFFF-26 |

## Edge Cases Handled

### No Company Assigned
```
Asset without company → XX-LAP-0001-26
```
Uses `XX` as default company code.

### Short Company Names
```
"AI Corp" → AI
"XY Company" → XY
```
Minimum 2 letters always maintained.

### Sequential Integrity
System finds highest existing counter and increments:
```
Existing: SH-LAP-0005-26
New:      SH-LAP-0006-26  ← Auto-incremented
```

## Benefits Over Old System

| Old Format | New Format | Benefit |
|------------|------------|---------|
| `AST-00001` | `SH-LAP-0001-26` | Instant identification |
| `AST-99999` (99,999 limit) | `FFFF` (65,535 per combo) | Much higher capacity |
| No category info | Category embedded | Quick categorization |
| No date context | Year embedded | Easy audit/tracking |
| 9 characters | 14 characters | Minimal length increase |

## Capacity Planning

### Per Company-Category-Year
- **65,535 assets** (hexadecimal FFFF)
- Counter resets annually

### Total System Capacity
```
10 Companies × 50 Categories × 1 Year = 32,767,500 assets/year
```

### Real-World Example
**Shamal Trading 2026:**
- Laptops: 0001 → FFFF (65,535 possible)
- Furniture: 0001 → FFFF (65,535 possible)
- Vehicles: 0001 → FFFF (65,535 possible)
- **Total: 196,605 assets** (for 3 categories)

## Implementation Details

### Automatic Generation Trigger
Asset ID is auto-generated when:
1. Creating new asset
2. `asset_tag` field is empty
3. Saves with format: `CO-CAT-XXXX-YY`

### Database Query
```python
# System automatically finds existing assets with same prefix+year
# Increments counter in hexadecimal
# Example: 0009 → 000A (not 0010)
```

### Uniqueness Constraint
```python
unique_together = [('organization', 'asset_tag')]
```
Ensures no duplicates within organization.

## Migration from Old System

### Existing Assets
- Old asset IDs (`AST-00001`) remain unchanged
- New assets use new format automatically
- Both formats coexist peacefully

### Manual Override
- Asset tag can still be manually entered if needed
- System only auto-generates when field is empty

## User Guide

### Creating Assets
1. Select **Company** (generates CO code)
2. Select **Category** (uses CAT code)
3. Leave **Asset ID** blank
4. Save → System generates: `CO-CAT-0001-26`

### Reading Asset IDs
```
SH-LAP-001A-26
│  │   │    │
│  │   │    └─ Year: 2026
│  │   └────── Counter: 26th asset (hex)
│  └────────── Category: Laptop
└───────────── Company: Shamal
```

### Searching Assets
- **By Company**: Search `SH-`
- **By Category**: Search `LAP-`
- **By Year**: Search `-26`
- **By Company+Category**: Search `SH-LAP-`

## Technical Specifications

### Code Location
- **File**: `apps/assets/models.py`
- **Function**: `generate_asset_tag(organization, category, company)`
- **Called from**: `Asset.save()` method

### Algorithm
1. Extract company code (2 chars from name)
2. Get category code (already exists)
3. Get current year suffix (last 2 digits)
4. Query existing assets with same prefix+year
5. Find max hexadecimal counter
6. Increment and format as 4-digit hex
7. Combine: `CO-CAT-XXXX-YY`

### Performance
- **O(n)** complexity for counter lookup
- Indexed queries on `asset_tag` field
- Efficient for 100K+ assets per organization

## Testing

Run test script:
```bash
python test_asset_id_generation.py
```

Test coverage:
- ✅ Company code generation
- ✅ Category code usage
- ✅ Sequential hex counter
- ✅ Year suffix
- ✅ Edge cases (no company, short names)
- ✅ Multiple assets per combination

## Summary

The new Asset ID format provides:
- 🎯 **Instant identification** of company and category
- 📈 **Scalability** for 65,535 assets per combination
- 🔄 **Automatic generation** with zero manual effort
- 📅 **Year tracking** built into the ID
- 🔍 **Easy searching** and filtering
- ✨ **Professional format** that's human-readable

**Format**: `CO-CAT-XXXX-YY` where each component has meaning and purpose!
