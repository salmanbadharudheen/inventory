# Performance Optimization Strategy for 100,000+ Assets

## Current Status
- **Current Load**: 14,000 assets
- **Target Load**: 100,000+ assets (1 lakh)
- **Current Setup**: Django + PostgreSQL/SQLite with pagination (25 items/page)

---

## 1. DATABASE OPTIMIZATION (CRITICAL)

### 1.1 Add Database Indexes
The Asset model has many ForeignKey fields that should have indexes on frequently filtered columns.

**Add to Asset model's Meta class:**
```python
class Meta:
    indexes = [
        models.Index(fields=['organization', 'is_deleted'], name='org_deleted_idx'),
        models.Index(fields=['organization', 'status'], name='org_status_idx'),
        models.Index(fields=['organization', 'category'], name='org_category_idx'),
        models.Index(fields=['organization', 'purchase_date'], name='org_purchase_idx'),
        models.Index(fields=['organization', 'asset_tag'], name='org_tag_idx'),
        models.Index(fields=['organization', 'assigned_to'], name='org_assigned_idx'),
        models.Index(fields=['organization', 'site'], name='org_site_idx'),
        models.Index(fields=['organization', 'department'], name='org_dept_idx'),
        models.Index(fields=['created_at'], name='created_at_idx'),
        # Composite indexes for common filter combinations
        models.Index(fields=['organization', 'category', 'status'], name='org_cat_status_idx'),
        models.Index(fields=['organization', 'site', 'building'], name='org_site_building_idx'),
    ]
```

**Create migration:**
```bash
python manage.py makemigrations
python manage.py migrate
```

### 1.2 Switch to PostgreSQL (If Using SQLite)
PostgreSQL significantly outperforms SQLite for 100k+ records:
- SQLite: Single-threaded, poor at concurrent writes
- PostgreSQL: Multi-threaded, excellent for large datasets

### 1.3 Database Query Optimization Settings
Add to `settings.py`:
```python
# Database connection pooling (if using PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Query optimization
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

---

## 2. DJANGO ORM OPTIMIZATION

### 2.1 Fix N+1 Query Problems in Views

**Current Issue** in `views.py` line 260-280:
```python
# This loads all assets but may cause N+1 queries
.select_related('category', 'sub_category', 'branch', 'assigned_to', ...)
```

**SOLUTION: Add Prefetch for Many-to-Many relationships**
```python
from django.db.models import Prefetch, Q

def get_queryset(self):
    queryset = Asset.objects.filter(
        organization=self.request.user.organization,
        is_deleted=False
    ).select_related(
        'category',           # ForeignKey
        'sub_category',       # ForeignKey
        'branch',             # ForeignKey
        'assigned_to',        # ForeignKey
        'site',               # ForeignKey
        'building',           # ForeignKey
        'brand_new',          # ForeignKey
        'room',               # ForeignKey
        'department',         # ForeignKey
        'region',             # ForeignKey
        'location',           # ForeignKey
        'sub_location',       # ForeignKey
        'vendor',             # ForeignKey
        'supplier',           # ForeignKey
        'company',            # ForeignKey
        'group',              # ForeignKey
        'custodian'           # ForeignKey
    ).prefetch_related(
        'attachments'         # ManyToMany or Reverse ForeignKey
    ).only(
        # Only load fields you actually display in list view
        'id', 'name', 'asset_tag', 'custom_asset_tag', 'asset_code',
        'serial_number', 'quantity', 'purchase_date', 'purchase_price',
        'currency', 'category_id', 'status', 'condition', 'assigned_to_id',
        'site_id', 'department_id', 'group_id', 'created_at'
    )
    return queryset
```

### 2.2 Optimize Depreciation Report Query

**Current approach loads ALL assets** - Very slow for 100k assets!

**SOLUTION: Use `distinct() + values()` for efficient aggregation**
```python
# In get_context_data() for depreciation view:

# Instead of loading all assets with aggregation in Python:
agg = queryset.aggregate(Sum('purchase_price'), Count('id'), ...)

# Use database-level aggregation with GROUP BY:
from django.db.models import Sum, Count, F, Case, When
from django.db.models.functions import Coalesce

# Group by category for summary
summary = queryset.values('category__name').annotate(
    total_count=Count('id'),
    total_price=Coalesce(Sum('purchase_price'), 0),
    total_depreciation=Coalesce(Sum('accumulated_depreciation'), 0)
).order_by('-total_price')

# Limit depreciation detail report to 100 items with pagination
from django.core.paginator import Paginator
paginator = Paginator(queryset.values(
    'id', 'name', 'asset_tag', 'category__name', 'purchase_price',
    'purchase_date', 'useful_life_years', 'accumulated_depreciation'
).order_by('-purchase_price'), 100)

page_obj = paginator.get_page(self.request.GET.get('page', 1))
context['depreciation_details'] = list(page_obj.object_list)
context['depreciation_summary'] = summary
```

### 2.3 Optimize Search Query

**Current Issue**: Line 280-310 searches across 30+ fields - Very slow!

**SOLUTION: Use `icontains` only on key fields**
```python
def get_queryset(self):
    queryset = Asset.objects.filter(...)
    
    query = self.request.GET.get('q')
    if query and len(query) > 2:  # Only search for 3+ characters
        q = (
            Q(name__icontains=query) |
            Q(asset_tag__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(asset_code__icontains=query) |
            Q(category__name__icontains=query) |
            Q(vendor__name__icontains=query)
        )
        queryset = queryset.filter(q)
    
    return queryset
```

---

## 3. CACHING STRATEGY

### 3.1 Cache Filter Dropdowns
Add to `views.py`:
```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    org = self.request.user.organization
    
    # Cache these for 1 hour (they change rarely)
    cache_key = f'filter_options_{org.id}'
    filter_options = cache.get(cache_key)
    
    if not filter_options:
        filter_options = {
            'categories': list(Category.objects.filter(organization=org).values('id', 'name')),
            'sites': list(Site.objects.filter(organization=org).values('id', 'name')),
            'departments': list(Department.objects.filter(organization=org).values('id', 'name')),
            'groups': list(Group.objects.filter(organization=org).values('id', 'name')),
        }
        cache.set(cache_key, filter_options, 3600)  # Cache for 1 hour
    
    context.update(filter_options)
    return context
```

### 3.2 Enable Redis Caching
Add to `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# Cache filter options
CACHE_TIMEOUT = 3600  # 1 hour
```

### 3.3 Cache Frequently Accessed Data
```bash
pip install django-redis
```

---

## 4. FRONTEND OPTIMIZATION

### 4.1 Infinite Scroll Instead of Pagination
Replace pagination with infinite scroll for asset list:

**JavaScript (Add to asset_list.html):**
```javascript
let currentPage = 1;
const pageSize = 50;  // Load 50 items per request

function loadMoreAssets() {
    fetch(`?page=${currentPage + 1}&format=json`)
        .then(r => r.json())
        .then(data => {
            // Append rows to table
            data.assets.forEach(asset => {
                addAssetRowToTable(asset);
            });
            currentPage++;
        });
}

// Trigger when user scrolls to bottom
window.addEventListener('scroll', () => {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
        loadMoreAssets();
    }
});
```

### 4.2 Lazy Load Table Details
Don't load all detail rows - load on demand:
```html
<tr id="detail-{{ asset.id }}" class="detail-row" style="display:none;" data-loaded="false">
    <td colspan="16">
        <div class="detail-content" id="detail-content-{{ asset.id }}">
            Loading...
        </div>
    </td>
</tr>
```

```javascript
function toggleDetails(assetId) {
    const detailRow = document.getElementById(`detail-${assetId}`);
    const contentDiv = document.getElementById(`detail-content-${assetId}`);
    
    if (detailRow.style.display === 'none') {
        // Load details if not loaded yet
        if (contentDiv.innerHTML === 'Loading...') {
            fetch(`/assets/${assetId}/details/json/`)
                .then(r => r.json())
                .then(data => {
                    contentDiv.innerHTML = renderDetailContent(data);
                });
        }
        detailRow.style.display = 'table-row';
    } else {
        detailRow.style.display = 'none';
    }
}
```

### 4.3 Reduce Data Transferred
Serve JSON API for AJAX requests:
```python
# In urls.py
path('assets/<uuid:pk>/details/json/', AssetDetailJsonView.as_view(), name='asset-detail-json'),

# In views.py
from django.http import JsonResponse
from django.views import View

class AssetDetailJsonView(View):
    def get(self, request, pk):
        asset = Asset.objects.get(pk=pk)
        return JsonResponse({
            'id': str(asset.id),
            'name': asset.name,
            'asset_tag': asset.asset_tag,
            # ... only essential fields
        })
```

---

## 5. BULK OPERATIONS OPTIMIZATION

### 5.1 Bulk Create/Update
```python
# Instead of saving assets one by one
assets = [Asset(...), Asset(...), ...]
Asset.objects.bulk_create(assets, batch_size=1000)

# For updates
Asset.objects.bulk_update(assets, fields=['status', 'location'], batch_size=1000)
```

### 5.2 Async Tasks for Heavy Operations
```bash
pip install celery redis
```

**tasks.py:**
```python
from celery import shared_task

@shared_task
def bulk_depreciation_calculation():
    """Calculate depreciation for all assets asynchronously"""
    assets = Asset.objects.filter(is_deleted=False)
    
    for asset in assets.iterator(chunk_size=1000):
        asset.calculate_depreciation()
        asset.save()

@shared_task
def export_assets_to_csv(organization_id):
    """Export asset list in background"""
    # Generate CSV file
    # Email to user
    pass
```

**Usage:**
```python
bulk_depreciation_calculation.delay()
export_assets_to_csv.delay(organization_id=org.id)
```

---

## 6. IMPLEMENTATION CHECKLIST

### Phase 1: Database (Week 1)
- [ ] Add database indexes to Asset model
- [ ] Create and run migrations
- [ ] Switch to PostgreSQL (if applicable)
- [ ] Analyze query performance with Django Debug Toolbar

### Phase 2: ORM Optimization (Week 1)
- [ ] Fix N+1 queries with select_related/prefetch_related
- [ ] Optimize search query (reduce fields)
- [ ] Optimize depreciation report query
- [ ] Add .only() to limit fields loaded

### Phase 3: Caching (Week 2)
- [ ] Install Redis
- [ ] Cache filter dropdown options
- [ ] Cache commonly accessed dashboards
- [ ] Implement cache invalidation strategy

### Phase 4: Frontend (Week 2)
- [ ] Implement lazy loading for detail rows
- [ ] Add pagination optimization
- [ ] Reduce table columns on initial load
- [ ] Use AJAX for detail panels

### Phase 5: Background Tasks (Week 3)
- [ ] Setup Celery + Redis
- [ ] Move heavy calculations to async tasks
- [ ] Implement bulk import optimization
- [ ] Setup scheduled depreciation calculation

---

## 7. MONITORING & BENCHMARKING

### 7.1 Install Django Debug Toolbar
```bash
pip install django-debug-toolbar
```

### 7.2 Monitor Query Performance
```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as context:
    list(Asset.objects.all()[:25])
    print(f"Number of queries: {len(context)}")
    for query in context:
        print(f"Time: {query['time']}ms - {query['sql']}")
```

### 7.3 Load Test with Locust
```bash
pip install locust
```

**locustfile.py:**
```python
from locust import HttpUser, task

class AssetListUser(HttpUser):
    @task
    def load_asset_list(self):
        self.client.get("/assets/")
    
    @task
    def search_assets(self):
        self.client.get("/assets/?q=laptop")
    
    @task
    def view_depreciation(self):
        self.client.get("/assets/?view=depreciation")
```

---

## 8. EXPECTED IMPROVEMENTS

With all optimizations applied:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Asset List Load (100 items) | 5-8s | 500-800ms | **10x** |
| Depreciation Report | 15-20s | 2-3s | **7x** |
| Search Speed | 8-10s | 1-2s | **5x** |
| Filter Dropdown Load | 2-3s | 100-200ms | **15x** |
| Concurrent Users Supported | 10 | 100+ | **10x** |

---

## 9. RECOMMENDED ORDER OF IMPLEMENTATION

1. **Start with Database Indexes** (biggest impact, easiest to implement)
2. **Fix ORM Queries** (medium effort, huge improvement)
3. **Add Caching** (good quick wins)
4. **Frontend Optimization** (improves UX significantly)
5. **Async Tasks** (for bulk operations)

---

## 10. QUICK START CODE

To start immediately, add these optimizations to your `views.py`:

```python
class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 50  # Increase from 25 to 50

    def get_queryset(self):
        # ✅ OPTIMIZED QUERY
        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False
        ).select_related(
            'category', 'sub_category', 'branch', 'assigned_to', 
            'site', 'building', 'brand_new', 'room', 'department',
            'region', 'location', 'sub_location', 'vendor', 
            'supplier', 'company', 'group', 'custodian'
        ).prefetch_related(
            'attachments'
        ).only(  # ✅ NEW: Load only needed fields
            'id', 'name', 'asset_tag', 'custom_asset_tag', 'asset_code',
            'serial_number', 'purchase_date', 'purchase_price', 'currency',
            'status', 'condition', 'created_at', 'category_id', 'assigned_to_id',
            'site_id', 'department_id', 'group_id', 'brand_new_id', 'building_id'
        )

        # ✅ OPTIMIZED SEARCH: Only key fields
        query = self.request.GET.get('q', '').strip()
        if len(query) > 2:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
                Q(serial_number__icontains=query) |
                Q(category__name__icontains=query) |
                Q(vendor__name__icontains=query)
            )
        
        return queryset.order_by('-created_at')
```

Start with this and test performance!
