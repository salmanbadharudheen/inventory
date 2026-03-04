# Asset Transfer Form - Quick Start Guide

## For Users

### Creating a New Asset Transfer

1. **Go to Asset Transfers**
   - Click "Asset Transfers" in the sidebar or navigate to `/assets/transfers/add/`

2. **Find Your Asset**
   - Enter the asset number/tag in the "Asset Number / Tag" field
   - Examples: `ASSET-001`, `LAP-123`, `PC-456`
   - Click the "Search" button or press Enter
   - The system will display the asset name when found

3. **Review Current Location (Auto-Populated)**
   - Region, Site, Building, Floor, Room automatically filled from asset's current location
   - Company and Custodian automatically filled from asset's current organization
   - These are shown for reference - you can edit if needed

4. **Specify New Location**
   - Select the "To Building" where the asset is going
   - The "To Floor" options will appear automatically
   - Select the "To Floor" where the asset is going
   - The "To Room" options will appear automatically
   - Optionally select "To Room" if needed
   - The system auto-fills "To Location" based on building selection

5. **Add Transfer Details**
   - **Movement Reason**: Why is this asset moving? (e.g., "Employee relocation", "Department reorganization")
   - **Request By**: Who is requesting this transfer (usually your name)
   - **Expected Receipt Date**: When should the asset arrive at the new location?
   - Any additional notes in the "Additional Notes" field

6. **Submit**
   - Click "Create Transfer" to submit
   - The transfer will be recorded with status "PENDING"

### Bulk Transfers

To process multiple asset transfers:
1. Enter asset #1, fill in destination, submit
2. Transfer created! Go back to Asset Transfers
3. Click "Create New" again
4. Repeat for next asset

The form is optimized for quick lookups, so you can process multiple transfers rapidly.

---

## For Administrators

### Understanding the New Form Structure

**From Section**: Shows the asset's current location and organization
- Region, Site, Building, Floor, Room: Location hierarchy where asset currently is
- Company & Custodian: Current ownership/responsibility information

**To Section**: Where the asset is moving to
- To Building → Floor → Room: Uses cascading dropdowns for accuracy
- To Location: Auto-populated based on building selection

**Movement Details**: Context and tracking
- Movement Reason: Specific business reason for transfer
- Request By: Who initiated the request (for audit trail)
- Expected Receipt Date: When transfer should complete

### Database Fields

New AssetTransfer fields stored in database:
```
transferred_from_region
transferred_from_site
transferred_from_building
transferred_from_floor
transferred_from_room
transferred_from_company
transferred_from_custodian
movement_reason
request_by
```

All are nullable to support legacy transfers and flexible entry.

### Configuration

**Asset lookup** works with any of these asset identifiers:
- `asset_tag` - The system-generated tag (e.g., "ASSET-001")
- `custom_asset_tag` - User-defined custom tag (e.g., "LAP-123")
- Name or code if exact tag not found

**Cascading selectors** use organization filtering to ensure data consistency:
- Building → Floor → Room selection prevents invalid combinations
- Location dropdown respects building selection

---

## Technical Details

### AJAX Endpoints Used
- `/assets/ajax/lookup/?asset_tag=ASSET-001` - Asset search
- `/locations/ajax/buildings/` - Get buildings for cascading selector
- `/locations/ajax/floors/?building_id=<id>` - Get floors in building
- `/locations/ajax/rooms/?floor_id=<id>` - Get rooms in floor
- `/assets/ajax/locations/?building_id=<id>` - Get locations in building

### Form Validation
- Asset field is required
- Location fields are optional (allows flexible entry)
- All date fields are optional

### Permissions
- Users can create transfers for assets in their organization
- Organizations are filtered automatically based on user's organization

---

## Troubleshooting

**Asset not found when searching:**
- Check the exact asset tag (case-insensitive but must match)
- Try searching with a partial name instead (e.g., "laptop" for "Dell Laptop")
- Ensure the asset is in your organization

**Cascading selectors not populating:**
- Make sure to select a "To Building" first
- Then the Floor dropdown will populate
- Then the Room dropdown will appear after selecting a Floor
- Location dropdown populates automatically from building selection

**Form not submitting:**
- Ensure an asset is selected (search and select an asset)
- All required date fields are valid
- Try clearing browser cache if dropdowns seem stuck

---

## Examples

### Example 1: Employee Promotion
```
Asset: LAPTOP-2024-001
From Location: Region: US, Site: NYC, Building: HQ, Floor: 3rd, Room: Office 301
Movement Reason: Employee promotion to manager
Request By: John Smith (HR)
To Building: HQ
To Floor: 4th
To Room: Conference Room 401
Expected Receipt Date: 2024-02-28
```

### Example 2: Department Reorganization
```
Asset: PC-MONITOR-456
From Location: Region: US, Site: Boston, Building: Tech Park, Floor: 2nd, Room: Dev Lab
Movement Reason: Department reorganization - consolidation
Request By: Sarah Johnson (Operations)
To Building: Tech Park
To Floor: 1st
To Room: Engineering Office
Expected Receipt Date: 2024-02-27
```

---

## Support

For questions or issues with asset transfers, contact your IT department or system administrator.
