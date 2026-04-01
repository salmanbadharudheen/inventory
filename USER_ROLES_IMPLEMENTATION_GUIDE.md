# User Roles - Implementation Guide

## Current Role System Overview

The inventory system uses a **4-tier role-based access control (RBAC)** system with a 2-level approval workflow.

---

## Current Roles (4 Active)

### 1. ADMIN
```
Database Value: ADMIN
Display: Admin
Superuser: Can be set to True
Access: Full system
```

### 2. SENIOR_MANAGER
```
Database Value: SENIOR_MANAGER
Display: Senior Manager
Superuser: Typically False
Access: Organization-wide, can do final approvals
```

### 3. CHECKER
```
Database Value: CHECKER
Display: Checker/Manager
Superuser: No
Access: Department/Organization level, first-level approvals only
```

### 4. EMPLOYEE
```
Database Value: EMPLOYEE
Display: Employee
Superuser: No
Access: Own data only
```

---

## How It Works - Current Implementation

### Code Location: [apps/users/models.py](apps/users/models.py)

```python
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        EMPLOYEE = 'EMPLOYEE', _('Employee')
        CHECKER = 'CHECKER', _('Checker/Manager')
        SENIOR_MANAGER = 'SENIOR_MANAGER', _('Senior Manager')
    
    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.EMPLOYEE
    )
```

### Helper Properties

```python
@property
def is_data_entry(self):
    return self.role == self.Role.EMPLOYEE

@property
def is_checker(self):
    return self.role == self.Role.CHECKER

@property
def is_senior_manager(self):
    return self.role == self.Role.SENIOR_MANAGER

@property
def can_approve(self):
    """Can do first-level approval"""
    return self.role in [
        self.Role.CHECKER,
        self.Role.SENIOR_MANAGER,
        self.Role.ADMIN
    ]

@property
def can_final_approve(self):
    """Can do final approval"""
    return self.role in [
        self.Role.SENIOR_MANAGER,
        self.Role.ADMIN
    ]
```

---

## Where Roles Are Used

### 1. Asset Views ([apps/assets/views.py](apps/assets/views.py))

#### Asset List - Queryset Filtering
```python
def get_queryset(self):
    user = self.request.user
    
    if user.role in [user.Role.SENIOR_MANAGER, user.Role.CHECKER]:
        # See all assets
        return Asset.objects.filter(
            organization=user.organization
        )
    elif user.is_superuser or user.role == user.Role.ADMIN:
        # See all assets
        return Asset.objects.filter(
            organization=user.organization
        )
    elif user.role == user.Role.EMPLOYEE:
        # See only own assets
        return Asset.objects.filter(
            organization=user.organization,
            created_by=user
        )
```

#### Asset Approval View
```python
def can_approve_asset(self, user):
    return (
        user.role in [user.Role.SENIOR_MANAGER, user.Role.CHECKER]
        and self.status == 'PENDING'
    ) or (
        (user.is_superuser or user.role == user.Role.ADMIN)
        and self.status == 'CHECKER_APPROVED'
    )
```

### 2. Disposal Views

#### Disposal List - Filtered by Role
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

### 3. User Views ([apps/users/views.py](apps/users/views.py))

#### Admin Dashboard
```python
def test_func(self):
    return self.request.user.is_superuser or \
           self.request.user.role == User.Role.ADMIN
```

#### Checker Dashboard
```python
def test_func(self):
    return self.request.user.is_checker or \
           self.request.user.is_superuser or \
           self.request.user.role == User.Role.ADMIN
```

#### Senior Manager Dashboard
```python
def test_func(self):
    return self.request.user.is_senior_manager or \
           self.request.user.is_superuser or \
           self.request.user.role == User.Role.ADMIN
```

#### Employee Views
```python
def test_func(self):
    return (
        self.request.user.role == User.Role.EMPLOYEE or
        self.request.user.is_superuser or
        self.request.user.role == User.Role.ADMIN
    )
```

---

## Approval Workflow - How It Currently Works

### 2-Tier Approval System

```
┌─────────────────────────────────────────────────────────────┐
│ EMPLOYEE submits Asset/Request                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │ Status: PENDING                   │
        │ Waiting for CHECKER approval      │
        └───────────┬───────────────────────┘
                    │
        ┌───────────▼──────────┬──────────────┐
        │                      │              │
    ✅ APPROVE           ❌ REJECT       (no action)
        │                      │
        ▼                      ▼
  CHECKER_APPROVED      REQUEST_REJECTED
        │
        ▼
┌──────────────────────────────┐
│ Status: CHECKER_APPROVED     │
│ Waiting for final approval   │
└──────────┬───────────────────┘
           │
  ┌────────▼──────────┬──────────────┐
  │                   │              │
✅FINAL APPROVE   ❌REJECT       (no action)
  │                   │
  ▼                   ▼
APPROVED         REJECTED
  │
  ▼
Asset/Request goes ACTIVE
```

### Code Location: [apps/assets/models.py](apps/assets/models.py#L600-L650)

```python
class ApprovalRequest(TenantAwareModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        CHECKER_APPROVED = 'CHECKER_APPROVED', _('Checker Approved')
        CHECKER_REJECTED = 'CHECKER_REJECTED', _('Checker Rejected')
        SENIOR_APPROVED = 'SENIOR_APPROVED', _('Senior Manager Approved')
        SENIOR_REJECTED = 'SENIOR_REJECTED', _('Senior Manager Rejected')
        APPROVED = 'APPROVED', _('Fully Approved')
        REJECTED = 'REJECTED', _('Rejected')
```

---

## Implementation Examples

### Example 1: Checking User Role in a View

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from apps.assets.models import Asset

class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 50
    
    def get_queryset(self):
        user = self.request.user
        base_qs = Asset.objects.filter(
            organization=user.organization
        )
        
        # Filter by role
        if user.role == user.Role.EMPLOYEE:
            # Employees see only their own assets
            return base_qs.filter(created_by=user)
        else:
            # Everyone else sees all organization assets
            return base_qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.get_role_display()
        context['can_create'] = True  # All roles can create
        context['can_approve'] = self.request.user.can_approve
        return context
```

### Example 2: Approval Logic

```python
class AssetApprovalView(LoginRequiredMixin, UpdateView):
    model = Asset
    
    def dispatch(self, request, *args, **kwargs):
        # Only approvers can access
        if not request.user.can_approve:
            messages.error(request, 'You cannot approve assets')
            return redirect('asset-list')
        
        asset = self.get_object()
        
        # Check approval status
        if asset.approval_status == 'PENDING':
            # CHECKER can approve PENDING
            if request.user.role not in [
                request.user.Role.CHECKER,
                request.user.Role.SENIOR_MANAGER,
                request.user.Role.ADMIN
            ]:
                messages.error(request, 'Not authorized')
                return redirect('asset-list')
        
        elif asset.approval_status == 'CHECKER_APPROVED':
            # Only SENIOR_MANAGER or ADMIN can do final approval
            if not request.user.can_final_approve:
                messages.error(request, 'Only senior managers can final-approve')
                return redirect('asset-list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = self.request.user
        asset = form.instance
        
        if user.role in [user.Role.CHECKER, user.Role.SENIOR_MANAGER]:
            # CHECKER approval
            if asset.approval_status == 'PENDING':
                asset.approval_status = 'CHECKER_APPROVED'
                asset.checker_approved_by = user
                asset.checker_approved_at = now()
        
        if user.can_final_approve:
            # Final approval
            if asset.approval_status == 'CHECKER_APPROVED':
                asset.approval_status = 'APPROVED'
                asset.approved_by = user
                asset.approved_at = now()
        
        return super().form_valid(form)
```

### Example 3: Template-Level Role Checking

```html
<!-- In asset_detail.html -->
<div class="card">
    <h3>Asset Details</h3>
    
    <!-- Show data to everyone -->
    <p>Name: {{ asset.name }}</p>
    <p>Category: {{ asset.category.name }}</p>
    
    <!-- Show approval section based on role -->
    {% if user.can_approve %}
        <div class="approval-section">
            <h4>Approval Actions</h4>
            
            {% if asset.approval_status == 'PENDING' %}
                <p>Status: Awaiting First-Level Approval</p>
                <form method="post">
                    {% csrf_token %}
                    <button name="action" value="approve" class="btn btn-success">
                        Approve
                    </button>
                    <button name="action" value="reject" class="btn btn-danger">
                        Reject
                    </button>
                </form>
            {% endif %}
            
            {% if asset.approval_status == 'CHECKER_APPROVED' and user.can_final_approve %}
                <p>Status: Awaiting Final Approval</p>
                <form method="post">
                    {% csrf_token %}
                    <button name="action" value="final_approve" class="btn btn-success">
                        Final Approve
                    </button>
                    <button name="action" value="final_reject" class="btn btn-danger">
                        Final Reject
                    </button>
                </form>
            {% endif %}
        </div>
    {% endif %}
</div>
```

---

## File Structure - Role Implementation

```
apps/
  users/
    models.py          ← User model with Role choices
    views.py           ← Dashboard views with role checks
    forms.py           ← User creation/edit forms
    
  assets/
    views.py           ← Asset views with queryset filtering
    models.py          ← Asset approval models
    
  locations/
    models.py          ← Department/Branch (role association)

templates/
  base.html           ← Role-based nav/menu
  users/
    admin_dashboard.html    ← Admin-only
    checker_dashboard.html  ← Checker-only
    employee_dashboard.html ← Employee-only
```

---

## Testing Roles

### Test User Creation

```python
from apps.users.models import User
from apps.core.models import Organization

# Create test org
org = Organization.objects.create(
    name='Test Org',
    slug='test-org'
)

# Create test users
employee = User.objects.create_user(
    username='emp',
    password='test123',
    organization=org,
    role=User.Role.EMPLOYEE
)

checker = User.objects.create_user(
    username='check',
    password='test123',
    organization=org,
    role=User.Role.CHECKER
)

senior = User.objects.create_user(
    username='senior',
    password='test123',
    organization=org,
    role=User.Role.SENIOR_MANAGER
)

admin = User.objects.create_user(
    username='admin',
    password='test123',
    organization=org,
    role=User.Role.ADMIN,
    is_staff=True,
    is_superuser=True
)
```

### Test Permissions

```python
# Test EMPLOYEE
assert employee.role == User.Role.EMPLOYEE
assert not employee.can_approve
assert not employee.can_final_approve

# Test CHECKER
assert checker.role == User.Role.CHECKER
assert checker.can_approve
assert not checker.can_final_approve

# Test SENIOR_MANAGER
assert senior.role == User.Role.SENIOR_MANAGER
assert senior.can_approve
assert senior.can_final_approve

# Test ADMIN
assert admin.role == User.Role.ADMIN
assert admin.can_approve
assert admin.can_final_approve
```

---

## Future Enhancement Ideas

### 1. Add AUDITOR Role
```python
class Role(models.TextChoices):
    ...
    AUDITOR = 'AUDITOR', _('Auditor')

@property
def is_auditor(self):
    return self.role == self.Role.AUDITOR

# Auditor can view all but cannot modify
```

### 2. Add ASSET_MANAGER Role
```python
class Role(models.TextChoices):
    ...
    ASSET_MANAGER = 'ASSET_MANAGER', _('Asset Manager')

@property
def is_asset_manager(self):
    return self.role == self.Role.ASSET_MANAGER

# Asset manager can manage categories, types, etc.
```

### 3. Granular Permissions
```python
class Permission(models.Model):
    role = models.ForeignKey(User.Role)
    feature = models.CharField()  # 'asset_view', 'asset_delete', etc.
    
# More fine-grained control per feature
```

### 4. Department-Based Access
```python
# Checker sees only their department
# Senior Manager sees their region
# Admin sees everything

def get_queryset(self):
    if self.user.role == CHECKER:
        return Asset.objects.filter(
            department=self.user.department
        )
```

---

## Summary Table

| Aspect | Current | Future |
|--------|---------|--------|
| **Active Roles** | 4 | 6+ |
| **Approval Levels** | 2-tier | 3+ tier |
| **Granularity** | Role-based | Permission-based |
| **Data Access** | Role wide | Department/Region |
| **Audit Trail** | Basic | Comprehensive |

---

## Key Takeaways

✅ **4 Active Roles**: ADMIN, SENIOR_MANAGER, CHECKER, EMPLOYEE
✅ **2-Tier Approvals**: CHECKER → SENIOR_MANAGER → ADMIN
✅ **Hierarchical Access**: Each role has specific access level
✅ **Multi-Layer Security**: View, Queryset, Template checks
✅ **Role Helper Properties**: `can_approve`, `can_final_approve`, etc.

---

## References

- [USER_ROLES_SYSTEM.md](USER_ROLES_SYSTEM.md) - Comprehensive documentation
- [USER_ROLES_QUICK_REFERENCE.md](USER_ROLES_QUICK_REFERENCE.md) - Quick lookup
- [apps/users/models.py](apps/users/models.py) - User model definition
- [apps/assets/views.py](apps/assets/views.py) - Role usage in views
