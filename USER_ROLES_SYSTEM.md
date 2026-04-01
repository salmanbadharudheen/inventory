# User Roles System - Current Implementation

## Overview
The system currently implements a **role-based access control (RBAC)** system with **4 primary user roles**. Each role has specific permissions and capabilities in the system.

## Current User Roles

### 1️⃣ **ADMIN** (Administrator)
- **Display Name**: Admin
- **Database Value**: `ADMIN`
- **Default Permissions**:
  - ✅ Full system access
  - ✅ Create, read, update, delete all assets
  - ✅ Manage users and roles
  - ✅ Manage organizations
  - ✅ Final approval of all requests
  - ✅ View all approval workflows
  - ✅ Configure system settings

**Used in Views**:
```python
user.is_superuser or user.role == User.Role.ADMIN
```

**Approval Levels**:
- ✅ Can approve/reject at FINAL stage
- ✅ Can approve after CHECKER approval
- ✅ Can also approve as CHECKER

---

### 2️⃣ **EMPLOYEE** (Regular Employee / Data Entry)
- **Display Name**: Employee
- **Database Value**: `EMPLOYEE`
- **Default Permissions**:
  - ✅ Create assets (with own data)
  - ✅ View own assets
  - ✅ Submit disposal requests
  - ✅ View own disposal requests
  - ✅ View own approval requests
  - ❌ Cannot approve anything
  - ❌ Cannot see other users' data
  - ❌ Cannot manage system

**Used in Views**:
```python
user.role == User.Role.EMPLOYEE
```

**Checkers**:
```python
@property
def is_data_entry(self):
    return self.role == self.Role.EMPLOYEE
```

**Approval Levels**:
- ❌ Cannot participate in approval workflow
- ❌ Can only submit requests

---

### 3️⃣ **CHECKER** (Manager / First Level Approver)
- **Display Name**: Checker/Manager
- **Database Value**: `CHECKER`
- **Default Permissions**:
  - ✅ Create assets
  - ✅ View all assets in department
  - ✅ Approve requests (first level)
  - ✅ View all approval requests
  - ✅ View all disposal requests
  - ✅ Can be assigned to department
  - ❌ Cannot do final approval
  - ❌ Cannot manage users
  - ❌ Cannot manage system

**Used in Views**:
```python
user.role == User.Role.CHECKER
user.is_checker
```

**Checkers**:
```python
@property
def is_checker(self):
    return self.role == self.Role.CHECKER

@property
def can_approve(self):
    return self.role in [self.Role.CHECKER, ...]
```

**Approval Levels**:
- ✅ Can approve at CHECKER stage
- ✅ Can first-level approve requests
- ❌ Cannot do final approval (only to SENIOR_MANAGER or ADMIN)

---

### 4️⃣ **SENIOR_MANAGER** (Senior Manager / Final Approver)
- **Display Name**: Senior Manager
- **Database Value**: `SENIOR_MANAGER`
- **Default Permissions**:
  - ✅ Create assets
  - ✅ View all assets
  - ✅ Approve requests (first AND final level)
  - ✅ View all approval workflows
  - ✅ View all disposal requests
  - ✅ View all approval requests
  - ✅ Override decisions
  - ❌ Cannot manage users
  - ❌ Cannot manage system settings

**Used in Views**:
```python
user.role == User.Role.SENIOR_MANAGER
user.is_senior_manager
```

**Checkers**:
```python
@property
def is_senior_manager(self):
    return self.role == self.Role.SENIOR_MANAGER

@property
def can_final_approve(self):
    return self.role in [self.Role.SENIOR_MANAGER, self.Role.ADMIN]
```

**Approval Levels**:
- ✅ Can approve at CHECKER stage
- ✅ Can approve at SENIOR_MANAGER (final) stage
- ✅ Can do final approval

---

## Role Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                        ADMIN                                │
│                  (System Administrator)                     │
│    Full access to everything, can override all decisions   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌──────▼──────────────┐         ┌──────────────▼──────┐
│   SENIOR_MANAGER    │         │      CHECKER        │
│  (Senior Manager)   │         │  (Department Head)  │
│ - First approval    │         │  - First approval   │
│ - Final approval    │         │  - Cannot final     │
│ - Can override      │         │  - Limited access   │
└─────────┬───────────┘         └────────┬────────────┘
          │                               │
          │                               │
          └───────────────┬───────────────┘
                          │
                          │
                  ┌───────▼────────┐
                  │    EMPLOYEE    │
                  │  (Regular User)│
                  │ - Submit only  │
                  │ - Own data     │
                  │ - No approval  │
                  └────────────────┘
```

---

## Permission Matrix

| Feature | EMPLOYEE | CHECKER | SENIOR_MANAGER | ADMIN |
|---------|----------|---------|----------------|-------|
| **Asset Management** |
| Create Asset | ✅ Own | ✅ All | ✅ All | ✅ All |
| Edit Asset | ✅ Own | ✅ All | ✅ All | ✅ All |
| Delete Asset | ❌ | ✅ | ✅ | ✅ |
| View Assets | ✅ Own | ✅ All | ✅ All | ✅ All |
| **Approvals** |
| First Approval | ❌ | ✅ | ✅ | ✅ |
| Final Approval | ❌ | ❌ | ✅ | ✅ |
| View Requests | ✅ Own | ✅ All | ✅ All | ✅ All |
| **Disposal** |
| Create Request | ✅ | ✅ | ✅ | ✅ |
| Approve Request | ❌ | ✅ | ✅ | ✅ |
| View All Requests | ❌ | ✅ | ✅ | ✅ |
| **User Management** |
| Create User | ❌ | ❌ | ❌ | ✅ |
| Edit User | ❌ | ❌ | ❌ | ✅ |
| Assign Roles | ❌ | ❌ | ❌ | ✅ |
| **System Config** |
| Manage Categories | ❌ | ❌ | ❌ | ✅ |
| Manage Organizations | ❌ | ❌ | ❌ | ✅ |
| View Reports | ❌ | ✅ | ✅ | ✅ |
| Dashboard Access | ✅ | ✅ | ✅ | ✅ |

---

## Approval Workflow

### Two-Tier Approval System

```
REQUEST SUBMITTED
       │
       ▼
   PENDING
       │
       ├─► CHECKER APPROVAL
       │        │
       │        ├─ ✅ APPROVED by CHECKER
       │        │        │
       │        │        ▼
       │        │   CHECKER_APPROVED
       │        │        │
       │        │        ▼
       │        │   SENIOR_MANAGER APPROVAL
       │        │        │
       │        │        ├─ ✅ APPROVED (FINAL)
       │        │        │
       │        │        └─ ❌ REJECTED
       │        │
       │        └─ ❌ REJECTED
       │
       └─► End of Workflow
```

### Role-Based Approval Flow

**EMPLOYEE**:
1. Submits request
2. Cannot approve
3. Waits for approval

**CHECKER**:
1. Reviews PENDING requests
2. ✅ Approves → moves to CHECKER_APPROVED
3. ❌ Rejects → request ends
4. Cannot do final approval

**SENIOR_MANAGER**:
1. Reviews PENDING requests (acts as CHECKER)
2. Approves PENDING → CHECKER_APPROVED
3. Reviews CHECKER_APPROVED requests
4. ✅ Final approval → APPROVED
5. ❌ Rejects → request ends

**ADMIN**:
1. Full access to all stages
2. Can override any decision
3. Can approve at any level
4. Can reassign approvals

---

## Helper Properties & Methods

### User Model Methods

```python
class User(AbstractUser):
    
    # Check role
    @property
    def is_data_entry(self):
        return self.role == self.Role.EMPLOYEE
    
    @property
    def is_checker(self):
        return self.role == self.Role.CHECKER
    
    @property
    def is_senior_manager(self):
        return self.role == self.Role.SENIOR_MANAGER
    
    # Can approve?
    @property
    def can_approve(self):
        """First level approval"""
        return self.role in [
            self.Role.CHECKER, 
            self.Role.SENIOR_MANAGER, 
            self.Role.ADMIN
        ]
    
    @property
    def can_final_approve(self):
        """Final approval"""
        return self.role in [
            self.Role.SENIOR_MANAGER, 
            self.Role.ADMIN
        ]
```

### Usage in Views

```python
# Check if user is checker
if user.is_checker:
    # Show checker actions
    
# Check if user can approve
if user.can_approve:
    # Show approve button
    
# Check if user can do final approval
if user.can_final_approve:
    # Show final approval button

# Check exact role
if user.role == User.Role.ADMIN:
    # Admin-only functionality
```

---

## Current Implementation in Views

### Asset Creation
```python
def get_queryset(self):
    user = self.request.user
    
    if user.role in [user.Role.SENIOR_MANAGER, user.Role.CHECKER]:
        # See all assets
        return Asset.objects.filter(organization=user.organization)
    elif user.is_superuser or user.role == user.Role.ADMIN:
        # See all assets
        return Asset.objects.filter(organization=user.organization)
    elif user.role == user.Role.EMPLOYEE:
        # See only own assets
        return Asset.objects.filter(
            organization=user.organization,
            created_by=user
        )
```

### Asset Approval
```python
def can_approve_asset(user, asset):
    # CHECKER can first-level approve
    if user.role in [user.Role.SENIOR_MANAGER, user.Role.CHECKER]:
        if asset.approval_status == 'PENDING':
            return True
    
    # ADMIN can do final approval
    if user.is_superuser or user.role == user.Role.ADMIN:
        if asset.approval_status == 'CHECKER_APPROVED':
            return True
    
    return False
```

### Disposal Requests
```python
def get_queryset(self):
    user = self.request.user
    
    # ADMIN: see all
    if user.is_superuser or user.role == user.Role.ADMIN:
        return AssetDisposal.objects.filter(
            organization=user.organization
        )
    
    # CHECKER/SENIOR_MANAGER: see all (can approve)
    elif user.role in [user.Role.CHECKER, user.Role.SENIOR_MANAGER]:
        return AssetDisposal.objects.filter(
            organization=user.organization
        )
    
    # EMPLOYEE: see own only
    elif user.role == user.Role.EMPLOYEE:
        return AssetDisposal.objects.filter(
            organization=user.organization,
            requested_by=user
        )
```

---

## How Roles Are Used Currently

### 1. Asset Management
- **EMPLOYEE**: Create/view own assets
- **CHECKER**: Create/edit/view all assets
- **SENIOR_MANAGER**: Create/edit/view all assets
- **ADMIN**: Full control

### 2. Approval Workflow
- **EMPLOYEE**: Submit, cannot approve
- **CHECKER**: First-level approval
- **SENIOR_MANAGER**: First + Final approval
- **ADMIN**: Override any approval

### 3. Disposal Requests
- **EMPLOYEE**: Submit own, view own
- **CHECKER**: View/approve all
- **SENIOR_MANAGER**: View/approve all
- **ADMIN**: Full control + override

### 4. Reporting
- **EMPLOYEE**: Limited dashboard
- **CHECKER**: Full reports for department
- **SENIOR_MANAGER**: Full organization reports
- **ADMIN**: System-wide reports

### 5. User Management
- **EMPLOYEE**: Cannot manage users
- **CHECKER**: Cannot manage users
- **SENIOR_MANAGER**: Cannot manage users
- **ADMIN**: Full user management

---

## Role Assignment

### Creating a New User

```python
user = User.objects.create_user(
    username='john_doe',
    email='john@example.com',
    organization=org,
    role=User.Role.EMPLOYEE,  # Default
    department=dept
)
```

### Changing User Role

```python
user.role = User.Role.CHECKER
user.save()

# User now has CHECKER permissions
```

### Role Display

```python
# In templates
{{ user.get_role_display }}  # Shows "Employee", "Admin", etc.

# In Python
user.get_role_display()  # Returns human-readable role name
```

---

## Security Checks

All views implement multi-layer security:

### View Level
```python
class AssetApprovalView(LoginRequiredMixin, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.can_approve):
            messages.error(request, 'Not permitted')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
```

### Queryset Level
```python
def get_queryset(self):
    # Filter by role
    if self.request.user.role == User.Role.EMPLOYEE:
        return Model.objects.filter(created_by=self.request.user)
    else:
        return Model.objects.filter(
            organization=self.request.user.organization
        )
```

### Template Level
```html
{% if user.can_approve %}
    <button class="approve-btn">Approve</button>
{% endif %}
```

---

## Unused/Deprecated Roles

The following roles were defined in migrations but are NOT currently used:

### AUDITOR (Deprecated)
```python
@property
def is_auditor(self):
    return False  # Not implemented
```

### ASSET_MANAGER (Deprecated)
```python
@property
def is_asset_manager(self):
    return False  # Not implemented
```

**Note**: These appear in the database schema but are not actively used in the codebase.

---

## Summary

### Current Role System
✅ **4 Active Roles**: ADMIN, EMPLOYEE, CHECKER, SENIOR_MANAGER
✅ **2-Tier Approval**: CHECKER → SENIOR_MANAGER → ADMIN
✅ **Role Hierarchy**: Clear permissions at each level
✅ **Multi-layer Security**: View + Queryset + Template checks
❌ **AUDITOR & ASSET_MANAGER**: Defined but not used

### Key Features
- ✅ Role-based access control (RBAC)
- ✅ Hierarchical approval workflows
- ✅ Department/Organization filtering
- ✅ Own-data vs. all-data access
- ✅ Admin override capability
- ✅ Helper properties for role checking

### Next Steps (For Enhancement)
1. **Implement AUDITOR role** - Read-only access to reports
2. **Implement ASSET_MANAGER role** - Manage asset configuration
3. **Add more granular permissions** - Per-feature permissions
4. **Add role-specific dashboards** - Custom views per role
5. **Add audit logging** - Track all role-based actions
6. **Add permission inheritance** - Dynamic permission assignment
