# Code Snippets Reference Guide

## 1. Dashboard View - show_financial Flag

### Location: `apps/assets/views.py` Lines 338-355

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    org = self.request.user.organization
    user = self.request.user
    
    # ✅ NEW: Determine if financial data should be shown
    show_financial = user.role != user.Role.EMPLOYEE
    context['show_financial'] = show_financial
    
    # Use only() to reduce database load for filter dropdowns
    context['categories'] = Category.objects.filter(organization=org).only('id', 'name').order_by('name')
    context['sites'] = Site.objects.filter(organization=org).only('id', 'name').order_by('name')
    # ... more filters ...
    
    # ✅ MODIFIED: Only process depreciation report if show_financial is True
    if self.request.GET.get('view') == 'depreciation' and show_financial:
        # Financial calculations here...
```

**Key Points:**
- `show_financial` is False when `user.role == 'EMPLOYEE'`
- `show_financial` is True for CHECKER, SENIOR_MANAGER, ADMIN
- Flag prevents expensive financial aggregations for data entry users

---

## 2. Dashboard Template - Financial Cards

### Location: `templates/dashboard.html` Lines 1101-1182

```django
<!-- Financial Stats - Hidden from EMPLOYEE role -->
{% if show_financial %}
<div class="stats-grid">
    <!-- TOTAL ASSETS - Always visible -->
    <div class="stat-card info">
        <div class="stat-card-header">
            <div class="stat-icon"><i data-lucide="package-check"></i></div>
        </div>
        <div class="stat-card-content">
            <div class="stat-label">Total Assets in Inventory</div>
            <div class="stat-value">{{ total_assets|intcomma }}</div>
            <div class="stat-meta">
                <i data-lucide="check" style="width: 14px; height: 14px;"></i>
                <span>Active inventory items</span>
            </div>
        </div>
    </div>

    <!-- TOTAL ACQUISITION COST - Hidden from EMPLOYEE -->
    <div class="stat-card">
        <div class="stat-card-header">
            <div class="stat-icon"><i data-lucide="wallet"></i></div>
        </div>
        <div class="stat-card-content">
            <div class="stat-label">Total Acquisition Cost</div>
            <div class="stat-value">AED {{ total_value|floatformat:0|intcomma }}</div>
            <div class="stat-meta">
                <i data-lucide="shield-check" style="width: 14px; height: 14px;"></i>
                <span>Secured Value</span>
            </div>
        </div>
    </div>

    <!-- NET BOOK VALUE - Hidden from EMPLOYEE -->
    <div class="stat-card success">
        <div class="stat-card-header">
            <div class="stat-icon"><i data-lucide="bar-chart-3"></i></div>
        </div>
        <div class="stat-card-content">
            <div class="stat-label">Net Book Value</div>
            <div class="stat-value">AED {{ total_nbv|floatformat:0|intcomma }}</div>
            <div class="stat-meta">
                <span>Current valuation</span>
            </div>
        </div>
    </div>

    <!-- TOTAL DEPRECIATION - Hidden from EMPLOYEE -->
    <div class="stat-card danger">
        <div class="stat-card-header">
            <div class="stat-icon"><i data-lucide="trending-down"></i></div>
        </div>
        <div class="stat-card-content">
            <div class="stat-label">Total Depreciation</div>
            <div class="stat-value">AED {{ total_depreciation|floatformat:0|intcomma }}</div>
            <div class="stat-meta">
                <span>{{ depreciation_percentage|floatformat:1 }}% lifecycle used</span>
            </div>
        </div>
    </div>
</div>

<!-- EMPLOYEE Dashboard - Only inventory count -->
{% else %}
<div class="stats-grid">
    <div class="stat-card info">
        <div class="stat-card-header">
            <div class="stat-icon"><i data-lucide="package-check"></i></div>
        </div>
        <div class="stat-card-content">
            <div class="stat-label">Total Assets in Inventory</div>
            <div class="stat-value">{{ total_assets|intcomma }}</div>
            <div class="stat-meta">
                <i data-lucide="check" style="width: 14px; height: 14px;"></i>
                <span>Active inventory items</span>
            </div>
        </div>
    </div>
</div>
{% endif %}
```

**Key Points:**
- When `show_financial=True`: All 4 cards visible (Managers)
- When `show_financial=False`: Only "Total Assets" card visible (Employees)

---

## 3. Asset Detail Template - Financial Summary

### Location: `templates/assets/asset_detail.html` Lines 118-128

```django
<!-- 5. Financial & Procurement -->
<div class="card detail-section">
    <div class="section-header"><i data-lucide="dollar-sign"></i><h3>Financial & Procurement</h3></div>
    
    <!-- ✅ Hidden from EMPLOYEE users -->
    {% if user.role != 'EMPLOYEE' %}
    <div class="financial-summary" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; padding: 1rem; background: #f8fafc; border-radius: 12px; margin-bottom: 1.5rem;">
        <div style="text-align: center;">
            <span class="detail-label">Purchase Price</span>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">{{ asset.currency }} {{ asset.purchase_price|default:"0.00" }}</div>
        </div>
        <div style="text-align: center;">
            <span class="detail-label">Current Value</span>
            <div style="font-size: 1.25rem; font-weight: 700; color: var(--primary);">{{ asset.currency }} {{ asset.current_value|default:"0.00" }}</div>
        </div>
        <div style="text-align: center;">
            <span class="detail-label">Accumulated Depr.</span>
            <div style="font-size: 1.25rem; font-weight: 700; color: #ef4444;">{{ asset.currency }} {{ asset.accumulated_depreciation|default:"0.00" }}</div>
        </div>
    </div>
    {% endif %}
    
    <!-- Rest of financial details still visible -->
    <div class="detail-grid">
        <div class="detail-item"><span class="detail-label">Purchase Date</span><span class="detail-value">{{ asset.purchase_date|date:"d M Y"|default:"-" }}</span></div>
        <div class="detail-item"><span class="detail-label">Invoice Number</span><span class="detail-value">{{ asset.invoice_number|default:"-" }}</span></div>
        <!-- ... more fields ... -->
    </div>
</div>
```

**Key Points:**
- Financial summary (3 boxes) is hidden from EMPLOYEE
- Rest of procurement details (dates, invoice, PO) remain visible
- Employees still see depreciation policy but not amounts

---

## 4. Asset List Template - Table Header

### Location: `templates/assets/asset_list.html` Lines 235-246

```django
<table class="premium-table">
    <thead>
        <tr>
            <th class="th-check">
                <input type="checkbox" id="select-all" class="form-check-input">
            </th>
            <th class="th-name">Asset Name</th>
            <th class="th-tag">Asset Tag</th>
            <th class="th-serial">Serial #</th>
            <th class="th-category">Category</th>
            <th class="th-brand">Brand</th>
            <th class="th-price">Purchase Price</th>
            <th class="th-group">Group</th>
            <th class="th-location">Site</th>
            <th class="th-sublocation">Location</th>
            <th class="th-department">Department</th>
            <th class="th-assigned">Assigned To</th>
            <th class="th-condition">Condition</th>
            <th class="th-status">Status</th>
            
            <!-- ✅ Hidden from EMPLOYEE users -->
            {% if user.role != 'EMPLOYEE' %}
            <th class="th-value">Value</th>
            {% endif %}
            
            <th class="th-actions">Actions</th>
        </tr>
    </thead>
    <tbody>
        <!-- ... table rows ... -->
    </tbody>
</table>
```

**Key Points:**
- "Value" column header only appears for non-EMPLOYEE users
- Table structure remains clean regardless of role
- All other columns visible to all users

---

## 5. Asset List Template - Table Row Value

### Location: `templates/assets/asset_list.html` Lines 318-328

```django
<tr class="table-row">
    <!-- ... previous columns ... -->
    
    <td class="td-status">
        <span class="badge-status status-{{ asset.status|lower }}">{{ asset.get_status_display }}</span>
    </td>
    
    <!-- ✅ Hidden from EMPLOYEE users -->
    {% if user.role != 'EMPLOYEE' %}
    <td class="td-value">
        {% if asset.purchase_price %}
        <span class="value-display">{{ asset.currency }} {{ asset.current_value }}</span>
        {% else %}
        <span class="no-value">-</span>
        {% endif %}
    </td>
    {% endif %}
    
    <td class="td-actions">
        <div class="action-buttons">
            <a href="{% url 'asset-detail' asset.pk %}" class="action-btn view-btn" title="View Details">
                <i data-lucide="eye"></i>
            </a>
            <!-- ... more actions ... -->
        </div>
    </td>
</tr>
```

**Key Points:**
- Each row's "Value" cell is conditionally rendered
- Only appears if user is NOT EMPLOYEE
- Actions column always visible

---

## 6. Asset List Template - Expanded Details

### Location: `templates/assets/asset_list.html` Lines 346-364

```django
<tr id="detail-{{ asset.id }}" class="detail-row" style="display:none;">
    <td colspan="16">
        <div class="detail-content">
            <div class="detail-left">
                <div class="asset-thumb">{{ asset.name|slice:":1"|upper }}</div>
                <div class="asset-main">
                    <div class="asset-name">{{ asset.name }}</div>
                    <div class="asset-sub">{{ asset.asset_tag }} {% if asset.serial_number %}• S/N {{ asset.serial_number }}{% endif %}</div>
                </div>
                
                <!-- ✅ Financial stats hidden from EMPLOYEE -->
                <div class="asset-stats">
                    {% if user.role != 'EMPLOYEE' %}
                    <div>
                        <div class="stat-label">NBV</div>
                        <div class="stat-value">{% if asset.purchase_price %}{{ asset.currency }} {{ asset.current_value }}{% else %}-{% endif %}</div>
                    </div>
                    <div>
                        <div class="stat-label">Accum. Dep.</div>
                        <div class="stat-value">{{ asset.accumulated_depreciation }}</div>
                    </div>
                    {% endif %}
                    
                    <!-- ✅ Status always visible -->
                    <div>
                        <div class="stat-label">Status</div>
                        <div class="stat-badge">{{ asset.get_status_display }}</div>
                    </div>
                </div>
            </div>
            
            <!-- ... rest of detail content ... -->
        </div>
    </td>
</tr>
```

**Key Points:**
- When user expands asset details, financial stats are hidden for EMPLOYEE
- Status badge always shows (operational information)
- Clean presentation regardless of role

---

## 7. User Model - Role Definition

### Location: `apps/users/models.py` Lines 6-10

```python
class Role(models.TextChoices):
    ADMIN = 'ADMIN', _('Admin')
    EMPLOYEE = 'EMPLOYEE', _('Data Entry')  # ✅ Updated display name
    CHECKER = 'CHECKER', _('Checker/Manager')
    SENIOR_MANAGER = 'SENIOR_MANAGER', _('Senior Manager')

@property
def is_data_entry(self):
    return self.role == self.Role.EMPLOYEE  # ✅ Convenient check
```

**Key Points:**
- Role value stays 'EMPLOYEE' (for backwards compatibility)
- Display name changed to 'Data Entry' (user-friendly)
- Helper property available: `user.is_data_entry`

---

## Quick Copy-Paste Patterns

### Hide from EMPLOYEE (in templates):
```django
{% if user.role != 'EMPLOYEE' %}
    <!-- Content hidden from employees -->
{% endif %}
```

### Show only to EMPLOYEE:
```django
{% if user.role == 'EMPLOYEE' %}
    <!-- Content visible only to employees -->
{% endif %}
```

### Use helper property:
```django
{% if not user.is_data_entry %}
    <!-- Content hidden from employees (using property) -->
{% endif %}
```

### In Python/Views:
```python
if user.role == user.Role.EMPLOYEE:
    # Employee user
else:
    # Non-employee user (Manager, Admin, etc.)
```

### Check if can access financial:
```python
show_financial = user.role != user.Role.EMPLOYEE
```

---

## Testing Template Syntax

### View Condition
```django
<!-- Test: Is user.role != 'EMPLOYEE'? -->
{% if user.role != 'EMPLOYEE' %}
<p>User is NOT an employee (can see financial data)</p>
{% else %}
<p>User IS an employee (cannot see financial data)</p>
{% endif %}
```

### Debug Output
```django
<!-- Add temporarily to template for debugging -->
<p>DEBUG: user.role = {{ user.role }}</p>
<p>DEBUG: user.is_data_entry = {{ user.is_data_entry }}</p>
<p>DEBUG: show_financial = {{ show_financial }}</p>
```

---

## Summary Table

| Component | Hide Pattern | User Group |
|-----------|-------------|-----------|
| Dashboard Cards | `{% if show_financial %}` | Total Cost, NBV, Depreciation |
| Asset Detail Summary | `{% if user.role != 'EMPLOYEE' %}` | Purchase Price, Current Value |
| Asset List Header | `{% if user.role != 'EMPLOYEE' %}` | Value column |
| Asset List Row | `{% if user.role != 'EMPLOYEE' %}` | Current value data |
| Asset List Expansion | `{% if user.role != 'EMPLOYEE' %}` | NBV, Accumulated Depreciation |

All patterns are consistent and easy to audit!
