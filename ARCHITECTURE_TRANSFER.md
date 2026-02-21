# Asset Transfer Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface Layer                   │
├─────────────────────────────────────────────────────────┤
│  Templates:                                              │
│  • transfer_list.html      - List & filter transfers    │
│  • transfer_form.html      - Create/Edit transfers      │
│  • transfer_detail.html    - View transfer details      │
│  • transfer_receive.html   - Confirm receipt            │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                   View Layer                             │
├─────────────────────────────────────────────────────────┤
│  • AssetTransferListView        GET  /assets/transfers/  │
│  • AssetTransferCreateView      POST /assets/transfers/add/
│  • AssetTransferDetailView      GET  /assets/transfers/<id>/
│  • AssetTransferUpdateView      POST /assets/transfers/<id>/edit/
│  • AssetTransferReceiveView     POST /assets/transfers/<id>/receive/
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                   Form Layer                             │
├─────────────────────────────────────────────────────────┤
│  • AssetTransferForm          - Create/Edit transfers   │
│  • AssetTransferReceiveForm   - Confirm receipt         │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                   Model Layer                            │
├─────────────────────────────────────────────────────────┤
│  AssetTransfer (TenantAwareModel)                        │
│  ├─ id (UUID PK)                                         │
│  ├─ asset (FK → Asset)                                  │
│  ├─ transfer_date (DateTime)                            │
│  ├─ transferred_from_user (FK)                          │
│  ├─ transferred_from_department (FK)                    │
│  ├─ transferred_from_location (FK)                      │
│  ├─ transferred_to_user (FK)                            │
│  ├─ transferred_to_department (FK)                      │
│  ├─ transferred_to_location (FK)                        │
│  ├─ status (Choices: PENDING, IN_TRANSIT, RECEIVED...)  │
│  ├─ transfer_reason (CharField)                         │
│  ├─ notes (TextField)                                   │
│  ├─ created_by (FK → User)                              │
│  ├─ received_by (FK → User)                             │
│  ├─ received_comments (TextField)                       │
│  ├─ created_at, updated_at (DateTime)                   │
│  └─ organization (FK → Organization) [TenantAware]      │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                   Admin Interface                        │
├─────────────────────────────────────────────────────────┤
│  AssetTransferAdmin                                      │
│  • List display, filters, search                        │
│  • Read-only timestamps and ID                          │
│  • Organized fieldsets                                  │
└─────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
User requests transfer
       ↓
AssetTransferCreateView (POST)
       ↓
AssetTransferForm validation
       ↓
Save to AssetTransfer model
       ↓
Redirect to transfer_detail.html
       ↓
User views transfer details
       ↓
User clicks "Receive" button
       ↓
AssetTransferReceiveView (GET)
       ↓
Shows transfer_receive.html
       ↓
User confirms receipt
       ↓
AssetTransferReceiveView (POST)
       ↓
Updates status to RECEIVED
       ↓
Updates received_by and actual_receipt_date
       ↓
Redirect back to transfer detail
```

## Status Workflow

```
┌─────────┐
│ PENDING │  ← Initial state when transfer created
└────┬────┘
     │
     ▼
┌──────────┐
│IN_TRANSIT│  ← Optional intermediate state
└────┬─────┘
     │
     ├──────────┐
     │           │
     ▼           ▼
┌─────────┐  ┌──────────┐
│RECEIVED │  │ REJECTED │  ← Final states
└─────────┘  └──────────┘

Also possible:
├──────────┐
│CANCELLED │  ← Cancelled before dispatch
└──────────┘
```

## Integration Points

### Related Models
- **Asset** - The item being transferred
- **User** - Creator, sender, receiver
- **Department** - Source/destination department
- **Location** - Source/destination location
- **Organization** - Tenant isolation

### Navigation Integration
- Added to sidebar under "Operations"
- Accessible from main asset views
- Quick access via navigation menu

### Admin Integration
- Full CRUD via Django admin
- List filtering and search
- Bulk operations possible
- Audit trail visible

## Permission Model

```
┌─────────────────────────────────────┐
│      Organization Isolation          │
├─────────────────────────────────────┤
│                                      │
│  User (Org A) ←→ Can only see       │
│  Transfers (Org A)                  │
│                                      │
│  User (Org B) ←→ Cannot see         │
│  Transfers (Org A)                  │
│                                      │
└─────────────────────────────────────┘
```

## Database Schema

```
AssetTransfer Table:
┌─────────────────────────────────────────────────┐
│ id (PK, UUID)                                   │
│ asset_id (FK → Asset)                          │
│ transfer_date (DateTime)                        │
│ expected_receipt_date (Date, Nullable)         │
│ actual_receipt_date (Date, Nullable)           │
│ transferred_from_user_id (FK, Nullable)        │
│ transferred_from_department_id (FK, Nullable)  │
│ transferred_from_location_id (FK, Nullable)    │
│ transferred_to_user_id (FK, Nullable)          │
│ transferred_to_department_id (FK, Nullable)    │
│ transferred_to_location_id (FK, Nullable)      │
│ status (CharField, Choices)                     │
│ transfer_reason (CharField)                     │
│ notes (TextField)                               │
│ received_comments (TextField)                   │
│ created_by_id (FK → User)                      │
│ received_by_id (FK → User, Nullable)           │
│ organization_id (FK → Organization)            │
│ created_at (DateTime)                          │
│ updated_at (DateTime)                          │
└─────────────────────────────────────────────────┘
```

## Query Optimization

### List View Queries
- Uses `select_related()` for:
  - asset
  - transferred_from_user
  - transferred_from_department
  - transferred_to_user
  - transferred_to_department
  - created_by

### Detail View Queries
- Fetches all related objects
- Minimizes N+1 queries
- Efficient for detail display

### Pagination
- 50 items per page
- Reduces memory usage
- Faster page loads

## API Accessibility

Currently accessible via:
- Web interface (forms and views)
- Django admin interface
- Direct model API (programmatically)

Future enhancements could add:
- REST API endpoints
- GraphQL support
- Mobile app integration

## Audit & Logging

All transfers include:
- Creator tracking (created_by)
- Receiver tracking (received_by)
- Timestamps (created_at, updated_at)
- Status history (visible in detail view)
- Comments from all parties
- Notes documentation

## Error Handling

Forms include:
- Required field validation
- Choice validation
- Foreign key validation
- Organization scoping validation

Views include:
- 404 handling for non-existent transfers
- 403 handling for organization mismatch
- Message feedback for user actions
- Redirect to appropriate pages

## Testing Checklist

- [ ] Can create transfer
- [ ] Can list transfers
- [ ] Can view transfer details
- [ ] Can edit pending transfer
- [ ] Can receive/reject transfer
- [ ] Status changes correctly
- [ ] Filters work properly
- [ ] Search works properly
- [ ] Organization isolation works
- [ ] Admin interface works
- [ ] Timestamps update correctly
- [ ] Users track correctly
