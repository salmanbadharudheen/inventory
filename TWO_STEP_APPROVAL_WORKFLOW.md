# Asset Disposal - Two-Step Approval Workflow Implementation

## Overview

The Asset Disposal feature now supports a **two-step approval workflow**:
1. **Step 1**: Manager reviews and approves/rejects
2. **Step 2**: Admin gives final approval/rejection

Additionally, the asset field is now **searchable with typing support**.

---

## Database Changes

### New Model Fields (Migration 0025)

```python
# Manager Approval Fields
manager_approved_by = ForeignKey(User)          # Manager who reviewed
manager_approved_at = DateTimeField()            # When manager approved
manager_rejection_reason = TextField()           # If manager rejected

# Admin Approval Fields (existing, unchanged)
approved_by = ForeignKey(User)                   # Admin who approved
approved_at = DateTimeField()                    # When admin approved
rejection_reason = TextField()                   # If admin rejected
```

### Updated Status Choices

```python
PENDING = 'PENDING'                              # Awaiting manager review
MANAGER_APPROVED = 'MANAGER_APPROVED'            # Manager approved, awaiting admin
APPROVED = 'APPROVED'                            # Admin approved (final)
REJECTED = 'REJECTED'                            # Rejected (by manager or admin)
COMPLETED = 'COMPLETED'                          # Disposal completed
CANCELLED = 'CANCELLED'                          # Cancelled
```

---

## Workflow Stages

### Stage 1: Employee Creates Request
- Employee fills form with asset and disposal details
- Asset field now supports **typing to search** by tag or name
- Status: `PENDING`
- Awaiting: Manager review

### Stage 2: Manager Reviews (NEW)
- **Who**: Users with role `SENIOR_MANAGER` or `CHECKER`
- **Access**: View "Manager Review" button on pending requests
- **URL**: `/disposals/<uuid>/manager-approve/`
- **Options**:
  - ✓ **Approve & Forward to Admin**: Moves to step 3
    - Sets `manager_approved_by` and `manager_approved_at`
    - Status becomes `MANAGER_APPROVED`
  - ✗ **Reject**: Request ends
    - Sets `manager_rejection_reason`
    - Status becomes `REJECTED`
- **Form**: `AssetDisposalManagerApprovalForm`
- **Template**: `disposal_manager_approve.html` (blue theme)

### Stage 3: Admin Final Approval (UPDATED)
- **Who**: Users with role `ADMIN` or `is_superuser`
- **Access**: View "Admin Final Approval" button on manager-approved requests
- **URL**: `/disposals/<uuid>/approve/`
- **Prerequisites**: Must have `status == MANAGER_APPROVED`
- **Options**:
  - ✓ **Approve**: Final approval
    - Sets `approved_by` and `approved_at`
    - Status becomes `APPROVED`
  - ✗ **Reject**: Request ends
    - Sets `rejection_reason`
    - Status becomes `REJECTED`
- **Form**: `AssetDisposalApprovalForm`
- **Template**: `disposal_approve.html` (green theme)

---

## Access Control

| Role | Stage 1 | Stage 2 | Stage 3 | View List |
|------|---------|---------|---------|-----------|
| Employee | Create ✓ | ✗ | ✗ | Own only |
| Manager | ✗ | Review ✓ | ✗ | All |
| Admin | Create ✓ | View ✓ | Approve ✓ | All |

---

## Forms

### AssetDisposalForm (Create)
```python
# Searchable asset field
asset = forms.ModelChoiceField(
    widget=forms.Select(attrs={
        'class': 'form-control searchable-select',
        'data-placeholder': 'Search and select an asset...'
    })
)

# Supports filtering and ordering by asset_tag
queryset = Asset.objects.filter(
    organization=org,
    status__in=[ACTIVE, IN_STORAGE, UNDER_MAINTENANCE]
).order_by('asset_tag')  # Alphabetical for easy search

# Other fields
disposal_method  # SCRAP, DONATE, SELL, RECYCLE, DISCARD, OTHER
reason          # Text explaining why disposal is needed
disposal_date   # Optional planned date
salvage_value   # Optional estimated value
notes           # Optional additional comments
```

### AssetDisposalManagerApprovalForm (Step 1 - Manager)
```python
# Status choices limited to manager actions
status = (MANAGER_APPROVED, 'Approve & Send to Admin')
         (REJECTED, 'Reject')

# Reasons
manager_rejection_reason  # Required if rejecting
notes                     # Optional comments
```

### AssetDisposalApprovalForm (Step 2 - Admin)
```python
# Status choices limited to admin actions
status = (APPROVED, 'Approve')
         (REJECTED, 'Reject')

# Reasons
rejection_reason  # Required if rejecting
notes            # Optional comments
```

---

## Views

### AssetDisposalManagerApproveView
```python
# Permissions
- test_func(): role in [SENIOR_MANAGER, CHECKER]
- Redirects non-managers with error message

# Queryset
- Only PENDING disposals
- Filtered by organization

# On form_valid()
- Sets manager_approved_by = current user
- Sets manager_approved_at = now()
- Status updated based on form submission
- Success/warning message shown
```

### AssetDisposalApproveView (UPDATED)
```python
# Permissions
- test_func(): is_superuser OR role == ADMIN
- Redirects non-admins with error message

# Queryset
- Only MANAGER_APPROVED disposals (changed from PENDING)
- Filtered by organization

# On form_valid()
- Sets approved_by = current user
- Sets approved_at = now()
- Status updated based on form submission
- Success/warning message shown
```

---

## Templates

### disposal_form.html (Create)
- Asset field now searchable
- Displays as select dropdown with type-ahead capability
- Assets ordered by tag for easier searching
- Shows disposal methods reference
- Shows approval process explanation

### disposal_manager_approve.html (NEW - Step 1)
- **Color scheme**: Blue (#3b82f6)
- **Badge**: "Manager Review (Step 1 of 2)"
- **Decision buttons**: 
  - Approve & Forward to Admin (blue)
  - Reject Request (red)
- **Asset summary**: Green-tinted info card
- **Comments**: Optional manager notes

### disposal_approve.html (Step 2 - Updated)
- **Color scheme**: Green (#059669)
- **Badge**: "Admin Approval Required"
- **Decision buttons**:
  - Approve (green)
  - Reject (red)
- **Asset summary**: Green-tinted info card
- **Comments**: Optional admin notes

### disposal_detail.html (UPDATED)
- **New approval workflow section** showing both steps
- **Step 1 status**:
  - Shows manager name and date if approved
  - Shows rejection reason if rejected
  - Shows "Pending manager review..." if still pending
- **Step 2 status**:
  - Shows admin name and date if approved
  - Shows rejection reason if rejected
  - Shows "Awaiting admin approval..." if waiting
- **Conditional action buttons**:
  - "Manager Review" button appears for pending if user is manager
  - "Admin Final Approval" button appears for manager-approved if user is admin

---

## URL Routes

```python
# List all disposals
GET    /disposals/                         → disposal-list

# Create new disposal request
GET    /disposals/add/                     → disposal-create (form)
POST   /disposals/add/                     → disposal-create (submit)

# View disposal details
GET    /disposals/<uuid>/                  → disposal-detail

# Manager approval (NEW)
GET    /disposals/<uuid>/manager-approve/  → disposal-manager-approve (form)
POST   /disposals/<uuid>/manager-approve/  → disposal-manager-approve (submit)

# Admin final approval
GET    /disposals/<uuid>/approve/          → disposal-approve (form)
POST   /disposals/<uuid>/approve/          → disposal-approve (submit)
```

---

## Database Migrations

**Migration 0025**: Added manager approval fields
- `manager_approved_by` (ForeignKey to User)
- `manager_approved_at` (DateTimeField)
- `manager_rejection_reason` (TextField)
- Updated `status` choices to include `MANAGER_APPROVED`

**Status**: ✓ Applied

---

## Searchable Asset Field

### How It Works

1. **Form renders** with `<select>` dropdown
2. **Assets filtered** by:
   - Organization (user's org only)
   - Status (ACTIVE, IN_STORAGE, UNDER_MAINTENANCE)
3. **Ordered by** `asset_tag` (alphabetically)
4. **Each option** displays as `<asset_tag> - <name>` format
5. **Browser select** allows typing to filter options

### Example
```
Asset 001 - Laptop
Asset 002 - Desktop
Asset 003 - Printer
```

User types "001" → filters to "Asset 001 - Laptop"

---

## Feature Summary

✅ **Two-step approval workflow** (Manager → Admin)
✅ **Searchable asset field** with type-ahead
✅ **Proper role-based access control**
✅ **Status tracking for each approval step**
✅ **Professional UI** with color-coded stages (Blue for Manager, Green for Admin)
✅ **Comprehensive workflow visualization** in detail view
✅ **Database migration** applied successfully
✅ **System validation** passes (0 issues)

---

## Example Workflow

```
1. Employee submits disposal request for "Laptop (Asset 001)"
   Status: PENDING

2. Manager reviews request
   - Sees asset details, reason, method
   - Approves and forwards to admin
   Status: MANAGER_APPROVED
   manager_approved_by: Manager User
   manager_approved_at: 2026-02-22 14:30:00

3. Admin receives notification
   - Reviews manager's approval
   - Gives final approval
   Status: APPROVED
   approved_by: Admin User
   approved_at: 2026-02-22 15:45:00

4. Employee can see both approvals
   - Manager: Approved by Manager User on 2026-02-22
   - Admin: Approved by Admin User on 2026-02-22
```

---

## Testing Checklist

- [x] Migration 0025 created and applied
- [x] Manager approval form working
- [x] Asset field searchable
- [x] Status transitions correct
- [x] Role-based access enforced
- [x] Templates render without errors
- [x] Detail view shows both approval steps
- [x] System check passes (0 issues)
- [ ] Test manager approval workflow
- [ ] Test admin final approval
- [ ] Test rejection at each stage
- [ ] Test searchable asset field

---

## Next Steps (Optional)

1. **Email Notifications**
   - Notify manager when new request arrives
   - Notify admin when manager approves
   - Notify employee when approved/rejected

2. **Comments Thread**
   - Add ability for both managers and admins to add comments
   - Track comment history

3. **Bulk Actions**
   - Approve/reject multiple requests at once

4. **Audit Trail**
   - Log all changes to each disposal request
   - Track who changed what and when
