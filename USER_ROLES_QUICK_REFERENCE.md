# User Roles Quick Reference

## 🎯 At a Glance

| Role | Level | Purpose | Can Approve | Can Final Approve |
|------|-------|---------|------------|------------------|
| **ADMIN** | System | System Administrator | ✅ YES | ✅ YES |
| **SENIOR_MANAGER** | Organization | Senior Manager | ✅ YES | ✅ YES |
| **CHECKER** | Department | Manager/Checker | ✅ YES | ❌ NO |
| **EMPLOYEE** | Individual | Regular User | ❌ NO | ❌ NO |

---

## 📊 Role Permissions Table

### Asset Operations
| Operation | EMPLOYEE | CHECKER | SENIOR_MGR | ADMIN |
|-----------|----------|---------|------------|-------|
| Create Asset | ✅ | ✅ | ✅ | ✅ |
| View Own Assets | ✅ | ✅ | ✅ | ✅ |
| View All Assets | ❌ | ✅ | ✅ | ✅ |
| Edit Asset | ❌ | ✅ | ✅ | ✅ |
| Delete Asset | ❌ | ❌ | ❌ | ✅ |
| Transfer Asset | ✅ | ✅ | ✅ | ✅ |

### Approval Operations
| Operation | EMPLOYEE | CHECKER | SENIOR_MGR | ADMIN |
|-----------|----------|---------|------------|-------|
| Submit Request | ✅ | ✅ | ✅ | ✅ |
| View Own Requests | ✅ | ✅ | ✅ | ✅ |
| View All Requests | ❌ | ✅ | ✅ | ✅ |
| First-Level Approve | ❌ | ✅ | ✅ | ✅ |
| Final Approve | ❌ | ❌ | ✅ | ✅ |
| Reject/Return | ❌ | ✅ | ✅ | ✅ |

### System Operations
| Operation | EMPLOYEE | CHECKER | SENIOR_MGR | ADMIN |
|-----------|----------|---------|------------|-------|
| View Reports | ❌ | ✅ | ✅ | ✅ |
| Manage Categories | ❌ | ❌ | ❌ | ✅ |
| Manage Users | ❌ | ❌ | ❌ | ✅ |
| Manage Organization | ❌ | ❌ | ❌ | ✅ |
| Configure System | ❌ | ❌ | ❌ | ✅ |
| Audit Log Access | ❌ | ❌ | ❌ | ✅ |

---

## 🔐 Security Model

### View-Level Protection
```python
# In assets/views.py
if not user.can_approve:
    return redirect('denied')
```

### Queryset-Level Filtering
```python
# Only show data user is authorized to see
if user.role == EMPLOYEE:
    queryset = Asset.objects.filter(created_by=user)
else:
    queryset = Asset.objects.filter(organization=user.organization)
```

### Template-Level Rendering
```html
<!-- Only render buttons user can use -->
{% if user.can_approve %}
    <button>Approve</button>
{% endif %}
```

---

## 🎓 Role Descriptions

### 👤 EMPLOYEE
**What they do**: Regular users who create and submit assets
**Permissions**:
- Create assets with their own details
- View only their own created assets
- Submit disposal/approval requests
- View status of their own requests
- Cannot approve anything

**Typical Users**: Office staff, technicians, data entry persons

---

### 👨‍💼 CHECKER
**What they do**: Department-level reviewers who approve first-stage requests
**Permissions**:
- Create and manage assets
- View all assets in the system
- Submit and approve first-level requests
- View all approval/disposal requests
- Cannot do final approval (must go to SENIOR_MANAGER)

**Typical Users**: Department heads, team leaders, managers

---

### 👨‍💻 SENIOR_MANAGER
**What they do**: Organization-level final decision maker
**Permissions**:
- Everything that CHECKER can do
- **PLUS**: Final-level approval authority
- Can override decisions
- Full access to all reports
- Cannot manage system configuration

**Typical Users**: Directors, senior managers, compliance officers

---

### 🔑 ADMIN
**What they do**: System administrator with complete control
**Permissions**:
- Everything (full system access)
- Override any decisions
- Create/edit/delete users
- Manage roles and permissions
- Configure system settings
- Full audit trail access

**Typical Users**: IT administrators, system owners

---

## 📋 Approval Workflow Example

### Scenario: Asset Creation Approval

```
EMPLOYEE creates asset
        │
        ▼
   PENDING (awaiting approval)
        │
        ▼
   CHECKER reviews
        │
        ├─ ✅ Approves
        │        │
        │        ▼
        │   CHECKER_APPROVED (awaiting final)
        │        │
        │        ▼
        │   SENIOR_MANAGER reviews
        │        │
        │        ├─ ✅ APPROVED (Done!)
        │        │
        │        └─ ❌ REJECTED (Back to EMPLOYEE)
        │
        └─ ❌ REJECTED (Back to EMPLOYEE)
```

---

## 💡 Use Case Examples

### Creating a New Asset

**EMPLOYEE**:
```
1. Form: Asset Name, Category, Details
2. Submit
3. System creates asset with role EMPLOYEE
4. Status: PENDING (needs approval)
5. Employee notified: "Awaiting Approval"
```

**CHECKER**:
```
1. Dashboard shows pending assets
2. Reviews employee's asset
3. Questions/concerns? Can email back
4. Clicks "Approve" if OK
5. Asset moves to SENIOR_MANAGER
```

**SENIOR_MANAGER**:
```
1. Dashboard shows checker-approved assets
2. Does final review
3. ✅ Clicks "Final Approve"
4. Asset Status → ACTIVE
5. EMPLOYEE notified: "Asset Approved!"
```

---

### Disposal Request

**EMPLOYEE**:
```
1. Selects asset to dispose
2. Reason: "End of life"
3. Submits request
4. Status: PENDING_APPROVAL
```

**CHECKER**:
```
1. Sees request in dashboard
2. Reviews reason
3. Approves (or sends back)
4. Request moves to SENIOR_MANAGER
```

**SENIOR_MANAGER**:
```
1. Final review of disposal
2. Approves with final authority
3. Request status: APPROVED
4. Asset can be disposed
```

---

## 🔄 Role-Based Views

### EMPLOYEE Dashboard
```
Dashboard
├── My Assets (created by me)
├── My Requests (submitted by me)
├── My Disposal Requests
└── Status of My Submissions
```

### CHECKER Dashboard
```
Dashboard
├── All Assets (for review/approve)
├── Pending Requests (to approve)
├── All Disposal Requests
├── Department Reports
└── Approval History
```

### SENIOR_MANAGER Dashboard
```
Dashboard
├── All Assets (organization-wide)
├── Checker-Approved Items (final review)
├── All Requests (complete view)
├── Organization Reports
├── Approval Analytics
└── Trend Analysis
```

### ADMIN Dashboard
```
Dashboard
├── System Overview
├── User Management
├── Organization Management
├── All Requests (all stages)
├── System Reports
├── Audit Logs
└── Configuration
```

---

## 🛡️ Security Features

### Multi-Layer Authorization
1. **View Level**: Check `can_approve` property
2. **Queryset Level**: Filter by `organization` and `role`
3. **Template Level**: Check role before rendering buttons
4. **Model Level**: Save `created_by` and `approved_by`

### Role Checking in Code

```python
# Bad (not secure)
if request.user.is_authenticated:
    # Do something

# Good (role-based)
if request.user.role == User.Role.CHECKER:
    # Do something

# Better (using properties)
if request.user.can_approve:
    # Do something

# Best (multi-layer)
def dispatch(self, request, *args, **kwargs):
    if not request.user.can_approve:
        return redirect('denied')
    return super().dispatch(request, *args, **kwargs)

def get_queryset(self):
    # Filter based on role
    if request.user.role == EMPLOYEE:
        return Asset.objects.filter(created_by=request.user)
    else:
        return Asset.objects.filter(
            organization=request.user.organization
        )
```

---

## 🎯 Role Assignment

### Creating Users with Different Roles

```python
# EMPLOYEE
emp = User.objects.create_user(
    username='john',
    role=User.Role.EMPLOYEE,
    organization=org
)

# CHECKER
checker = User.objects.create_user(
    username='jane',
    role=User.Role.CHECKER,
    organization=org,
    department=dept
)

# SENIOR_MANAGER
senior = User.objects.create_user(
    username='bob',
    role=User.Role.SENIOR_MANAGER,
    organization=org
)

# ADMIN
admin = User.objects.create_user(
    username='admin',
    role=User.Role.ADMIN,
    is_staff=True,
    is_superuser=True
)
```

---

## 📊 Statistics

- **Total Roles**: 4 active, 2 deprecated
- **Approval Levels**: 2-tier (CHECKER → SENIOR_MANAGER → ADMIN)
- **Role Checks**: Used in 50+ views
- **Security Layers**: 3 (view, queryset, template)

---

## ⚠️ Deprecated Roles (Not Implemented)

### AUDITOR
- Defined in `User.Role` choices
- Status: `return False`
- Future: Read-only access to reports

### ASSET_MANAGER  
- Defined in `User.Role` choices
- Status: `return False`
- Future: Manage asset configuration

---

## 🔧 Common Implementation Patterns

### Pattern 1: Check Single Role
```python
if user.role == User.Role.ADMIN:
    # Admin-only code
```

### Pattern 2: Check Multiple Roles
```python
if user.role in [User.Role.CHECKER, User.Role.SENIOR_MANAGER]:
    # Checker or Senior Manager
```

### Pattern 3: Use Helper Properties
```python
if user.can_approve:
    # Show approve button
    
if user.can_final_approve:
    # Show final approve button
```

### Pattern 4: Combine with is_superuser
```python
if user.is_superuser or user.role == User.Role.ADMIN:
    # Full admin access
```

---

## 📝 Database Representation

```sql
-- User roles are stored as text choices
role VARCHAR(50) DEFAULT 'EMPLOYEE'
CHECK (role IN ('ADMIN', 'EMPLOYEE', 'CHECKER', 'SENIOR_MANAGER', 'AUDITOR', 'ASSET_MANAGER'))

-- Examples
user@example.com → EMPLOYEE
manager@example.com → CHECKER
director@example.com → SENIOR_MANAGER
admin@example.com → ADMIN
```

---

## ✅ Checklist for Role Implementation

### When Creating a New Feature:
- [ ] Check user role in view dispatch
- [ ] Filter queryset by role
- [ ] Hide UI elements in template if not authorized
- [ ] Log who did what (created_by, approved_by)
- [ ] Add role-based tests
- [ ] Document role requirements

### When Assigning Roles:
- [ ] Verify organization assignment
- [ ] Assign department if CHECKER
- [ ] Set appropriate permissions
- [ ] Send welcome email with role info
- [ ] Document access levels

---

## 🎓 Summary

**4 Active Roles**: ADMIN → SENIOR_MANAGER → CHECKER → EMPLOYEE

**Permission Pyramid**:
```
        ▲
        │ ADMIN (Full)
        │ ├─ SENIOR_MANAGER (Org-wide)
        │ ├─ CHECKER (Department)
        │ └─ EMPLOYEE (Own data)
        │
   Least ├──── Most
   Power │ Power
```

**Security**: View + Queryset + Template checks

**Approvals**: 2-tier (CHECKER first, then SENIOR_MANAGER)

**Data Access**: EMPLOYEE sees own only, others see organization-wide

---

## 🔗 Related Files

- Model: `apps/users/models.py`
- Views: `apps/assets/views.py` (role checks)
- Templates: `templates/base.html`, `templates/assets/*`
- Helpers: `User.is_checker`, `User.can_approve`, etc.

