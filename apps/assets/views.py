from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
import csv
import io
from .models import (Asset, AssetAttachment, Category, SubCategory, Vendor, generate_asset_tag,
                     Group, SubGroup, Brand, Company, Supplier, Custodian, AssetRemarks, AssetTransfer)
from .forms import (AssetForm, CategoryForm, SubCategoryForm, VendorForm, AssetImportForm,
                    GroupForm, SubGroupForm, BrandForm, CompanyForm, SupplierForm, CustodianForm, AssetRemarksForm, AssetTransferForm, AssetTransferReceiveForm)
from django.db import transaction
from apps.locations.models import (Branch, Building, Floor, Room, 
                                   Region, Site, Location, SubLocation, Department)
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from decimal import Decimal
from datetime import date, datetime
import openpyxl

def get_subcategories(request):
    category_id = request.GET.get('category_id')
    if category_id:
        subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    return JsonResponse([], safe=False)

def get_departments(request):
    branch_id = request.GET.get('branch_id')
    if branch_id:
        from apps.locations.models import Department
        departments = Department.objects.filter(branch_id=branch_id).values('id', 'name')
        return JsonResponse(list(departments), safe=False)
    return JsonResponse([], safe=False)

def get_buildings(request):
    branch_id = request.GET.get('branch_id')
    if branch_id:
        buildings = Building.objects.filter(branch_id=branch_id).values('id', 'name')
        return JsonResponse(list(buildings), safe=False)
    return JsonResponse([], safe=False)

def get_floors(request):
    building_id = request.GET.get('building_id')
    if building_id:
        floors = Floor.objects.filter(building_id=building_id).values('id', 'name')
        return JsonResponse(list(floors), safe=False)
    return JsonResponse([], safe=False)

def get_rooms(request):
    floor_id = request.GET.get('floor_id')
    if floor_id:
        rooms = Room.objects.filter(floor_id=floor_id).values('id', 'name')
        return JsonResponse(list(rooms), safe=False)
    return JsonResponse(list(rooms), safe=False)

def lookup_asset(request):
    # Support lookup by free-text `q` (tag/name/code) or by explicit `asset_id`.
    asset_id = request.GET.get('asset_id')
    query = request.GET.get('q')

    asset = None
    org = getattr(request.user, 'organization', None)

    if asset_id:
        try:
            asset = Asset.objects.select_related(
                'department', 'branch', 'building', 'floor', 'room',
                'region', 'site', 'location', 'sub_location', 'assigned_to'
            ).get(id=asset_id, organization=org)
        except Asset.DoesNotExist:
            asset = None

    elif query:
        # Prioritize exact match on tags, then partial on name
        asset = Asset.objects.filter(
            Q(asset_tag__iexact=query) | 
            Q(custom_asset_tag__iexact=query) |
            Q(asset_code__iexact=query),
            organization=org
        ).first()

        if not asset:
            # Fallback to name search if no exact tag match
            asset = Asset.objects.filter(
                name__icontains=query,
                organization=org
            ).first()

    if not asset:
        return JsonResponse({'error': 'Not found'}, status=404)

    # Current location/ownership details
    assigned = None
    if asset.assigned_to:
        assigned = {'id': asset.assigned_to.id, 'name': asset.assigned_to.get_full_name() or asset.assigned_to.username}

    current = {
        'id': str(asset.id),
        'name': asset.name,
        'asset_tag': asset.asset_tag,
        'department': {'id': asset.department.id, 'name': asset.department.name} if asset.department else None,
        'branch': {'id': asset.branch.id, 'name': asset.branch.name} if asset.branch else None,
        'building': {'id': asset.building.id, 'name': asset.building.name} if asset.building else None,
        'floor': {'id': asset.floor.id, 'name': asset.floor.name} if asset.floor else None,
        'room': {'id': asset.room.id, 'name': asset.room.name} if asset.room else None,
        'region': {'id': asset.region.id, 'name': asset.region.name} if getattr(asset, 'region', None) else None,
        'site': {'id': asset.site.id, 'name': asset.site.name} if getattr(asset, 'site', None) else None,
        'location': {'id': asset.location.id, 'name': asset.location.name} if getattr(asset, 'location', None) else None,
        'sub_location': {'id': asset.sub_location.id, 'name': asset.sub_location.name} if getattr(asset, 'sub_location', None) else None,
        'assigned_to': assigned,
        'status': asset.status,
    }

    # Available transfer options (simple lists to populate selects)
    departments = list(Department.objects.filter(organization=org).values('id', 'name')) if org else []
    locations = list(Location.objects.filter(organization=org).values('id', 'name')) if org else []
    users = []
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = list(User.objects.filter(organization=org).values('id', 'first_name', 'last_name', 'username')) if org else []
        # normalize to id/name
        users = [{'id': u['id'], 'name': (u['first_name'] + ' ' + u['last_name']).strip() or u['username']} for u in users]
    except Exception:
        users = []

    return JsonResponse({'asset': current, 'departments': departments, 'locations': locations, 'users': users})

ASSET_IMPORT_FIELDS = [
    'name', 'description', 'short_description', 'asset_tag', 'custom_asset_tag', 
    'asset_code', 'erp_asset_number', 'quantity', 'label_type', 'serial_number', 
    'category', 'sub_category', 'asset_type', 'group', 'sub_group', 'brand', 
    'model', 'condition', 'status', 'department', 'cost_center', 'company', 
    'supplier', 'vendor', 'custodian', 'employee_number', 'branch', 'building', 
    'floor', 'room', 'region', 'site', 'location', 'sub_location', 'purchase_date', 
    'purchase_price', 'currency', 'invoice_number', 'invoice_date', 'po_number', 
    'po_date', 'do_number', 'do_date', 'grn_number', 'warranty_start', 'warranty_end', 
    'tagged_date', 'date_placed_in_service', 'insurance_start_date', 'insurance_end_date', 
    'maintenance_start_date', 'maintenance_end_date', 'next_maintenance_date', 
    'maintenance_frequency_days', 'expected_units', 'useful_life_years', 
    'salvage_value', 'depreciation_method', 'remarks', 'notes'
]

def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_assets.csv"'

    writer = csv.writer(response)
    writer.writerow(ASSET_IMPORT_FIELDS)
    
    # Sample Row
    writer.writerow([
        'Laptop Dell XPS', 'High-end laptop', 'Dell XPS 15', '', 'TAG-001',
        'C001', 'ERP-100', '1', 'NON_METAL', 'SN123456', 
        'IT', 'Laptops', 'TAGGABLE', 'IT Equipment', 'Computers', 'Dell', 
        'XPS 15', 'NEW', 'ACTIVE', 'IT Dept', 'CC-101', 'ABC Corp', 
        'Tech Supplies Ltd', 'Main Vendor', 'EMP001', 'E123', 'Main Branch', 'HQ Building', 
        '2nd Floor', 'Room 201', 'North Region', 'Main Site', 'Main Location', 'Sub 1', '2023-01-01', 
        '5000', 'AED', 'INV-001', '2023-01-01', 'PO-100', 
        '2022-12-15', 'DO-100', '2022-12-28', 'GRN-100', '2023-01-01', '2026-01-01', 
        '2023-01-02', '2023-01-10', '2023-01-01', '2024-01-01', 
        '2023-01-01', '2024-01-01', '2023-06-01', '180', '1000', '5', '500', 
        'STRAIGHT_LINE', 'Needs Setup', 'Initial deployment'
    ])
    
    return response

def download_sample_excel(request):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Assets"

    # Header
    ws.append(ASSET_IMPORT_FIELDS)

    # Sample Row
    ws.append([
        'Laptop Dell XPS', 'High-end laptop', 'Dell XPS 15', '', 'TAG-001',
        'C001', 'ERP-100', 1, 'NON_METAL', 'SN123456', 
        'IT', 'Laptops', 'TAGGABLE', 'IT Equipment', 'Computers', 'Dell', 
        'XPS 15', 'NEW', 'ACTIVE', 'IT Dept', 'CC-101', 'ABC Corp', 
        'Tech Supplies Ltd', 'Main Vendor', 'EMP001', 'E123', 'Main Branch', 'HQ Building', 
        '2nd Floor', 'Room 201', 'North Region', 'Main Site', 'Main Location', 'Sub 1', '2023-01-01', 
        5000, 'AED', 'INV-001', '2023-01-01', 'PO-100', 
        '2022-12-15', 'DO-100', '2022-12-28', 'GRN-100', '2023-01-01', '2026-01-01', 
        '2023-01-02', '2023-01-10', '2023-01-01', '2024-01-01', 
        '2023-01-01', '2024-01-01', '2023-06-01', '180', '1000', '5', '500', 
        'STRAIGHT_LINE', 'Needs Setup', 'Initial deployment'
    ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sample_assets.xlsx"'
    wb.save(response)
    return response

# --- ASSET VIEWS ---
class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 25

    def get_template_names(self):
        if self.request.GET.get('view') == 'depreciation':
            return ['assets/depreciation_report.html']
        return ['assets/asset_list.html']

    def get_queryset(self):
        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False
        ).select_related(
            'category', 'branch', 'assigned_to', 
            'site', 'building', 'brand_new', 'room'
        )

        # Search across many asset fields and common related names
        query = self.request.GET.get('q')
        if query:
            q = (
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
                Q(custom_asset_tag__icontains=query) |
                Q(asset_code__icontains=query) |
                Q(erp_asset_number__icontains=query) |
                Q(serial_number__icontains=query) |
                Q(model__icontains=query) |
                Q(brand__icontains=query) |
                Q(brand_new__name__icontains=query) |
                Q(category__name__icontains=query) |
                Q(sub_category__name__icontains=query) |
                Q(vendor__name__icontains=query) |
                Q(supplier__name__icontains=query) |
                Q(company__name__icontains=query) |
                Q(invoice_number__icontains=query) |
                Q(po_number__icontains=query) |
                Q(grn_number__icontains=query) |
                Q(do_number__icontains=query) |
                Q(tagged_date__icontains=query) |
                Q(purchase_date__icontains=query) |
                Q(department__name__icontains=query) |
                Q(branch__name__icontains=query) |
                Q(building__name__icontains=query) |
                Q(room__name__icontains=query) |
                Q(site__name__icontains=query) |
                Q(region__name__icontains=query) |
                Q(location__name__icontains=query) |
                Q(sub_location__name__icontains=query) |
                Q(assigned_to__username__icontains=query) |
                Q(assigned_to__first_name__icontains=query) |
                Q(assigned_to__last_name__icontains=query) |
                Q(notes__icontains=query)
            )

            queryset = queryset.filter(q)
            
        # Advanced Filters
        filters = {
            'status': 'status',
            'category': 'category_id',
            'site': 'site_id',
            'building': 'building_id',
            'brand': 'brand_new_id',
            'department': 'department_id',
            'subcategory': 'sub_category_id',
            'group': 'group_id',
        }
        
        for param, field in filters.items():
            val = self.request.GET.get(param)
            if val:
                queryset = queryset.filter(**{field: val})
        
        # Date Range Filters
        purchase_date_from = self.request.GET.get('purchase_date_from')
        purchase_date_to = self.request.GET.get('purchase_date_to')
        
        if purchase_date_from:
            queryset = queryset.filter(purchase_date__gte=purchase_date_from)
        if purchase_date_to:
            queryset = queryset.filter(purchase_date__lte=purchase_date_to)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        
        # Dropdown data for filters
        context['categories'] = Category.objects.filter(organization=org).order_by('name')
        context['sites'] = Site.objects.filter(organization=org).order_by('name')
        context['buildings'] = Building.objects.filter(organization=org).order_by('name')
        context['brands'] = Brand.objects.filter(organization=org).order_by('name')
        context['departments'] = Department.objects.filter(organization=org).order_by('name')
        context['subcategories'] = SubCategory.objects.filter(organization=org).order_by('name')
        context['groups'] = Group.objects.filter(organization=org).order_by('name')
        context['statuses'] = Asset.Status.choices

        if self.request.GET.get('view') == 'depreciation':
            # Calculate totals for the visible queryset (respects filters)
            queryset = self.get_queryset()
            all_visible = list(queryset)
            
            total_cost = sum((a.purchase_price or Decimal('0')) for a in all_visible)
            total_acc_dep = sum(a.accumulated_depreciation for a in all_visible)
            total_nbv = sum(a.current_value for a in all_visible)
            
            context['total_cost'] = total_cost
            context['total_acc_dep'] = total_acc_dep
            context['total_nbv'] = total_nbv
            context['is_report'] = True
            
        # Ensure filters persist during pagination
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()
            
        return context

class BulkAssetActionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        asset_ids = request.POST.getlist('asset_ids')
        action = request.POST.get('action')
        
        if not asset_ids:
            messages.warning(request, "No assets selected.")
            return redirect('asset-list')
            
        assets = Asset.objects.filter(
            id__in=asset_ids, 
            organization=request.user.organization
        )
        
        count = assets.count()
        
        if action == 'delete':
            assets.update(is_deleted=True)
            messages.success(request, f"Successfully deleted {count} assets.")
        elif action.startswith('status_'):
            new_status = action.replace('status_', '').upper()
            assets.update(status=new_status)
            messages.success(request, f"Successfully updated status for {count} assets.")
            
        return redirect('asset-list')

class ExportAssetExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # We reuse the logic from AssetListView to respect current filters
        view = AssetListView()
        view.request = request
        queryset = view.get_queryset()
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Assets Export"
        
        headers = [
            'Asset Tag', 'Name', 'Category', 'Status', 
            'Site', 'Building', 'Room', 'Condition', 
            'Purchase Price', 'Currency', 'Purchase Date'
        ]
        ws.append(headers)
        
        for asset in queryset:
            ws.append([
                asset.asset_tag,
                asset.name,
                asset.category.name if asset.category else '',
                asset.get_status_display(),
                asset.site.name if asset.site else '',
                asset.building.name if asset.building else '',
                str(asset.room) if asset.room else '',
                asset.get_condition_display(),
                float(asset.purchase_price) if asset.purchase_price else 0,
                asset.currency,
                asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else ''
            ])
            
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="assets_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response

class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('asset-list')

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception:
            import traceback
            print(traceback.format_exc())
            raise

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception:
            import traceback
            print(traceback.format_exc())
            raise

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        # Auto-generate Asset Tag if empty
        if not form.instance.asset_tag:
            form.instance.asset_tag = generate_asset_tag(self.request.user.organization)
        return super().form_valid(form)


class AssetImportView(LoginRequiredMixin, FormView):
    template_name = 'assets/asset_import.html'
    form_class = AssetImportForm
    success_url = reverse_lazy('asset-list')

    def get_file_data(self, uploaded_file):
        """Extract data rows from CSV or Excel file efficiently."""
        data = []
        filename = uploaded_file.name.lower()
        
        if filename.endswith('.csv'):
            try:
                # Use a generator or list but decoded efficiently
                decoded_file = uploaded_file.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                data = list(reader)
            except Exception as e:
                raise ValueError(f"Error reading CSV: {str(e)}")
        
        elif filename.endswith('.xlsx'):
            try:
                # Optimized Excel reading for large files
                wb = openpyxl.load_workbook(uploaded_file, data_only=True, read_only=True)
                sheet = wb.active
                
                # Get headers from the first row
                rows_gen = sheet.iter_rows(values_only=True)
                headers = [h for h in next(rows_gen) if h]
                
                for row in rows_gen:
                    if any(row):  # Skip empty rows
                        row_dict = dict(zip(headers, row))
                        data.append(row_dict)
                wb.close() # Important for read_only=True
            except Exception as e:
                raise ValueError(f"Error reading Excel: {str(e)}")
        
        return data

    def parse_date(self, value):
        if not value:
            return None
        if isinstance(value, (datetime, date)):
            return value
        val_str = str(value).strip()
        if not val_str or val_str.lower() in ('none', 'null', 'nan'):
            return None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S'):
            try:
                return datetime.strptime(val_str, fmt).date()
            except (ValueError, TypeError):
                continue
        return None

    def form_valid(self, form):
        import_file = form.cleaned_data['import_file']
        org = self.request.user.organization
        
        try:
            rows = self.get_file_data(import_file)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

        if not rows:
            messages.warning(self.request, "No data found in the file.")
            return self.form_invalid(form)

        # --- PRE-FETCH MASTER DATA (CACHING) ---
        def build_cache(model, field='name', org_relevant=True):
            qs = model.objects.all()
            if org_relevant and hasattr(model, 'organization'):
                qs = qs.filter(organization=org)
            elif org_relevant and hasattr(model, 'category') and hasattr(model.category, 'organization'):
                # For SubCategory if it didn't have direct org link (it does, but just in case)
                qs = qs.filter(category__organization=org)
            
            cache = {}
            for obj in qs:
                val = getattr(obj, field)
                if val:
                    cache[str(val).strip().lower()] = obj
            return cache

        # Asset-specific master data
        categories_by_code = build_cache(Category, 'code')
        categories_by_name = build_cache(Category, 'name')
        subcategories = build_cache(SubCategory, 'name')
        groups = build_cache(Group, 'name')
        subgroups = build_cache(SubGroup, 'name')
        brands = build_cache(Brand, 'name')
        companies = build_cache(Company, 'name')
        suppliers = build_cache(Supplier, 'name')
        vendors = build_cache(Vendor, 'name')
        remarks = build_cache(AssetRemarks, 'remark')
        
        # Custodians (Lookup by Employee ID or Username)
        custodians_by_eid = build_cache(Custodian, 'employee_id')
        # Custodian by username requires related lookup
        custodians_by_user = {
            str(c.user.username).lower(): c 
            for c in Custodian.objects.filter(organization=org).select_related('user') 
            if c.user
        }

        # Location master data
        branches = build_cache(Branch, 'name')
        buildings = build_cache(Building, 'name')
        floors = build_cache(Floor, 'name')
        rooms = build_cache(Room, 'name')
        regions = build_cache(Region, 'name')
        sites = build_cache(Site, 'name')
        locations = build_cache(Location, 'name')
        sub_locations = build_cache(SubLocation, 'name')
        departments = build_cache(Department, 'name')

        # Helper to avoid repetitive dictionary lookups
        def get_from_cache(cache, val):
            if val is None: return None
            return cache.get(str(val).strip().lower())

        errors = []
        assets_to_create = []

        # --- SEQUENTIAL ASSET TAG GENERATION ---
        # Robustly find the next serial number
        start_tag_num = 0
        tag_prefix = "AST-"
        # Optimized: only fetch tags that match the expected format
        existing_tags = Asset.objects.filter(
            organization=org, 
            asset_tag__startswith=tag_prefix
        ).values_list('asset_tag', flat=True)
        
        for tag in existing_tags:
            try:
                # Expecting AST-XXXXX
                suffix = tag[len(tag_prefix):]
                num = int(suffix)
                if num > start_tag_num: start_tag_num = num
            except (ValueError, IndexError, TypeError):
                continue
        
        current_tag_num = start_tag_num + 1

        for row_idx, row in enumerate(rows, start=2):
            try:
                # 1. Identification
                name = str(row.get('name') or '').strip()
                if not name:
                    raise ValueError("Asset Name is required.")

                cat_val = str(row.get('category') or '').strip()
                category = get_from_cache(categories_by_code, cat_val) or get_from_cache(categories_by_name, cat_val)
                if not category:
                    raise ValueError(f"Category '{cat_val}' not found.")

                asset_tag = str(row.get('asset_tag') or '').strip()
                if not asset_tag:
                    asset_tag = f"AST-{current_tag_num:05d}"
                    current_tag_num += 1

                # 2. Enums / Choices
                def get_choice(val, choices_model, default):
                    if val is None: return default
                    v = str(val).strip().upper()
                    if v in choices_model.values: return v
                    # Search by display name if possible? 
                    # For now just upper-case exact match with choices
                    return default

                status = get_choice(row.get('status'), Asset.Status, Asset.Status.ACTIVE)
                condition = get_choice(row.get('condition'), Asset.Condition, Asset.Condition.NEW)
                asset_type = get_choice(row.get('asset_type'), Asset.Type, Asset.Type.TAGGABLE)
                label_type = get_choice(row.get('label_type'), Asset.LabelType, Asset.LabelType.NON_METAL)

                # 3. Master Data Lookups (from cache)
                sub_category = get_from_cache(subcategories, row.get('sub_category'))
                group = get_from_cache(groups, row.get('group'))
                sub_group = get_from_cache(subgroups, row.get('sub_group'))
                brand_new = get_from_cache(brands, row.get('brand'))
                company = get_from_cache(companies, row.get('company'))
                supplier = get_from_cache(suppliers, row.get('supplier'))
                vendor = get_from_cache(vendors, row.get('vendor'))
                
                # Custodian lookup (EID then Username)
                cust_val = row.get('custodian')
                custodian = get_from_cache(custodians_by_eid, cust_val) or get_from_cache(custodians_by_user, cust_val)
                
                asset_remarks = get_from_cache(remarks, row.get('remarks'))

                # 4. Location Details (from cache)
                branch = get_from_cache(branches, row.get('branch'))
                department = get_from_cache(departments, row.get('department'))
                building = get_from_cache(buildings, row.get('building'))
                floor = get_from_cache(floors, row.get('floor'))
                room = get_from_cache(rooms, row.get('room'))
                
                # Special case: Auto-create room if missing but floor exists
                if not room and floor and row.get('room'):
                    room_name = str(row.get('room')).strip()
                    room = Room.objects.create(organization=org, floor=floor, name=room_name)
                    # Add to cache to prevent duplicate creation in this session
                    rooms[room_name.lower()] = room

                region = get_from_cache(regions, row.get('region'))
                site = get_from_cache(sites, row.get('site'))
                location = get_from_cache(locations, row.get('location'))
                sub_location = get_from_cache(sub_locations, row.get('sub_location'))

                # 5. Numerical Parsing
                def parse_decimal(val):
                    if val is None or str(val).strip() == '': return None
                    try: return Decimal(str(val).replace(',', ''))
                    except: return None
                
                def parse_int(val, default=None):
                    if val is None or str(val).strip() == '': return default
                    try: return int(float(str(val)))
                    except: return default

                # Create Asset Instance (in memory)
                asset = Asset(
                    organization=org,
                    created_by=self.request.user,
                    name=name,
                    description=str(row.get('description') or ''),
                    short_description=str(row.get('short_description') or ''),
                    asset_tag=asset_tag,
                    custom_asset_tag=row.get('custom_asset_tag'),
                    asset_code=row.get('asset_code'),
                    erp_asset_number=row.get('erp_asset_number'),
                    quantity=parse_int(row.get('quantity'), 1),
                    label_type=label_type,
                    serial_number=row.get('serial_number'),
                    category=category,
                    sub_category=sub_category,
                    asset_type=asset_type,
                    status=status,
                    condition=condition,
                    group=group,
                    sub_group=sub_group,
                    brand_new=brand_new,
                    brand=str(row.get('brand') or '')[:100],
                    model=str(row.get('model') or '')[:100],
                    department=department,
                    cost_center=str(row.get('cost_center') or '')[:100],
                    company=company,
                    supplier=supplier,
                    vendor=vendor,
                    custodian=custodian,
                    employee_number=str(row.get('employee_number') or '')[:100],
                    branch=branch,
                    building=building,
                    floor=floor,
                    room=room,
                    region=region,
                    site=site,
                    location=location,
                    sub_location=sub_location,
                    purchase_date=self.parse_date(row.get('purchase_date')),
                    purchase_price=parse_decimal(row.get('purchase_price')),
                    currency=str(row.get('currency') or 'AED')[:10],
                    invoice_number=str(row.get('invoice_number') or '')[:100],
                    invoice_date=self.parse_date(row.get('invoice_date')),
                    po_number=str(row.get('po_number') or '')[:100],
                    po_date=self.parse_date(row.get('po_date')),
                    do_number=str(row.get('do_number') or '')[:100],
                    do_date=self.parse_date(row.get('do_date')),
                    grn_number=str(row.get('grn_number') or '')[:100],
                    warranty_start=self.parse_date(row.get('warranty_start')),
                    warranty_end=self.parse_date(row.get('warranty_end')),
                    tagged_date=self.parse_date(row.get('tagged_date')),
                    date_placed_in_service=self.parse_date(row.get('date_placed_in_service')),
                    insurance_start_date=self.parse_date(row.get('insurance_start_date')),
                    insurance_end_date=self.parse_date(row.get('insurance_end_date')),
                    maintenance_start_date=self.parse_date(row.get('maintenance_start_date')),
                    maintenance_end_date=self.parse_date(row.get('maintenance_end_date')),
                    next_maintenance_date=self.parse_date(row.get('next_maintenance_date')),
                    maintenance_frequency_days=parse_int(row.get('maintenance_frequency_days'), 0),
                    expected_units=parse_int(row.get('expected_units')),
                    useful_life_years=parse_int(row.get('useful_life_years')),
                    salvage_value=parse_decimal(row.get('salvage_value')),
                    depreciation_method=str(row.get('depreciation_method') or '').upper() or None,
                    asset_remarks=asset_remarks,
                    notes=str(row.get('notes') or '')
                )

                # Performance: Manually apply inheritance from category (since bulk_create bypasses save())
                if asset.category:
                    if asset.useful_life_years in (None, 0):
                        asset.useful_life_years = asset.category.useful_life_years
                    if not asset.depreciation_method:
                        asset.depreciation_method = asset.category.depreciation_method
                    if asset.salvage_value is None or asset.salvage_value == 0:
                        asset.salvage_value = asset.category.default_salvage_value
                    if asset.depreciation_method == 'UNITS_OF_PRODUCTION' and not asset.expected_units:
                        asset.expected_units = asset.category.default_expected_units

                assets_to_create.append(asset)

            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")

        if errors:
            # Display limited errors to avoid overwhelming the message system
            for err in errors[:15]:
                messages.error(self.request, err)
            if len(errors) > 15:
                messages.error(self.request, f"...and {len(errors) - 15} more errors.")
            return self.form_invalid(form)

        # --- BULK SAVE ---
        try:
            with transaction.atomic():
                # Process in batches of 1000 for stability
                Asset.objects.bulk_create(assets_to_create, batch_size=1000)
                messages.success(self.request, f"Successfully imported {len(assets_to_create)} assets.")
        except Exception as e:
            messages.error(self.request, f"Database error during bulk save: {str(e)}")
            return self.form_invalid(form)

        return redirect(self.success_url)

class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    template_name = 'assets/asset_detail.html'
    context_object_name = 'asset'

    def get_queryset(self):
        return Asset.objects.filter(
            organization=self.request.user.organization
        ).select_related(
            'category', 'sub_category', 'group', 'sub_group',
            'brand_new', 'department', 'assigned_to', 'company',
            'supplier', 'custodian', 'branch', 'building', 'floor',
            'room', 'region', 'site', 'location', 'sub_location',
            'vendor', 'asset_remarks'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import date
        context['today'] = date.today()
        return context

class AssetUpdateView(LoginRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('asset-list')

    def get_queryset(self):
        return Asset.objects.filter(organization=self.request.user.organization)


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        # Auto-generate Asset Tag if empty
        if not form.instance.asset_tag:
            form.instance.asset_tag = generate_asset_tag(self.request.user.organization)
        return super().form_valid(form)

# --- CATEGORY VIEWS ---
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'assets/configuration/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(organization=self.request.user.organization)

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'assets/configuration/category_form.html'
    success_url = reverse_lazy('category-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'assets/configuration/category_form.html'
    success_url = reverse_lazy('category-list')
    
    def get_queryset(self):
        return Category.objects.filter(organization=self.request.user.organization)

# --- SUBCATEGORY VIEWS ---
class SubCategoryListView(LoginRequiredMixin, ListView):
    model = SubCategory
    template_name = 'assets/configuration/subcategory_list.html'
    context_object_name = 'subcategories'

    def get_queryset(self):
        return SubCategory.objects.filter(category__organization=self.request.user.organization).select_related('category')

class SubCategoryCreateView(LoginRequiredMixin, CreateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = 'assets/configuration/subcategory_form.html'
    success_url = reverse_lazy('subcategory-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

class SubCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = 'assets/configuration/subcategory_form.html'
    success_url = reverse_lazy('subcategory-list')
    
    def get_queryset(self):
        # Ensure user can only edit subcategories in their org
        return SubCategory.objects.filter(category__organization=self.request.user.organization)

# --- VENDOR VIEWS ---
class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = 'assets/configuration/vendor_list.html'
    context_object_name = 'vendors'

    def get_queryset(self):
        return Vendor.objects.filter(organization=self.request.user.organization)

class VendorCreateView(LoginRequiredMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'assets/configuration/vendor_form.html'
    success_url = reverse_lazy('vendor-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class VendorUpdateView(LoginRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'assets/configuration/vendor_form.html'
    success_url = reverse_lazy('vendor-list')
    
    def get_queryset(self):
        return Vendor.objects.filter(organization=self.request.user.organization)

# New Master Data CRUD Views

# --- GROUP VIEWS ---
class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'assets/configuration/group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return Group.objects.filter(organization=self.request.user.organization)

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'assets/configuration/group_form.html'
    success_url = reverse_lazy('group-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class GroupUpdateView(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'assets/configuration/group_form.html'
    success_url = reverse_lazy('group-list')
    
    def get_queryset(self):
        return Group.objects.filter(organization=self.request.user.organization)

# --- SUBGROUP VIEWS ---
class SubGroupListView(LoginRequiredMixin, ListView):
    model = SubGroup
    template_name = 'assets/configuration/subgroup_list.html'
    context_object_name = 'subgroups'

    def get_queryset(self):
        return SubGroup.objects.filter(group__organization=self.request.user.organization).select_related('group')

class SubGroupCreateView(LoginRequiredMixin, CreateView):
    model = SubGroup
    form_class = SubGroupForm
    template_name = 'assets/configuration/subgroup_form.html'
    success_url = reverse_lazy('subgroup-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

class SubGroupUpdateView(LoginRequiredMixin, UpdateView):
    model = SubGroup
    form_class = SubGroupForm
    template_name = 'assets/configuration/subgroup_form.html'
    success_url = reverse_lazy('subgroup-list')
    
    def get_queryset(self):
        return SubGroup.objects.filter(group__organization=self.request.user.organization)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

# --- BRAND VIEWS ---
class BrandListView(LoginRequiredMixin, ListView):
    model = Brand
    template_name = 'assets/configuration/brand_list.html'
    context_object_name = 'brands'

    def get_queryset(self):
        return Brand.objects.filter(organization=self.request.user.organization)

class BrandCreateView(LoginRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'assets/configuration/brand_form.html'
    success_url = reverse_lazy('brand-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class BrandUpdateView(LoginRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'assets/configuration/brand_form.html'
    success_url = reverse_lazy('brand-list')
    
    def get_queryset(self):
        return Brand.objects.filter(organization=self.request.user.organization)

# --- COMPANY VIEWS ---
class CompanyListView(LoginRequiredMixin, ListView):
    model = Company
    template_name = 'assets/configuration/company_list.html'
    context_object_name = 'companies'

    def get_queryset(self):
        return Company.objects.filter(organization=self.request.user.organization)

class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'assets/configuration/company_form.html'
    success_url = reverse_lazy('company-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'assets/configuration/company_form.html'
    success_url = reverse_lazy('company-list')
    
    def get_queryset(self):
        return Company.objects.filter(organization=self.request.user.organization)

# --- SUPPLIER VIEWS ---
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'assets/configuration/supplier_list.html'
    context_object_name = 'suppliers'

    def get_queryset(self):
        return Supplier.objects.filter(organization=self.request.user.organization)

class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'assets/configuration/supplier_form.html'
    success_url = reverse_lazy('supplier-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'assets/configuration/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    
    def get_queryset(self):
        return Supplier.objects.filter(organization=self.request.user.organization)

# --- CUSTODIAN VIEWS ---
class CustodianListView(LoginRequiredMixin, ListView):
    model = Custodian
    template_name = 'assets/configuration/custodian_list.html'
    context_object_name = 'custodians'

    def get_queryset(self):
        return Custodian.objects.filter(organization=self.request.user.organization).select_related('user')

class CustodianCreateView(LoginRequiredMixin, CreateView):
    model = Custodian
    form_class = CustodianForm
    template_name = 'assets/configuration/custodian_form.html'
    success_url = reverse_lazy('custodian-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class CustodianUpdateView(LoginRequiredMixin, UpdateView):
    model = Custodian
    form_class = CustodianForm
    template_name = 'assets/configuration/custodian_form.html'
    success_url = reverse_lazy('custodian-list')
    
    def get_queryset(self):
        return Custodian.objects.filter(organization=self.request.user.organization)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

# --- ASSET REMARKS VIEWS ---
class AssetRemarksListView(LoginRequiredMixin, ListView):
    model = AssetRemarks
    template_name = 'assets/configuration/assetremarks_list.html'
    context_object_name = 'remarks'

    def get_queryset(self):
        return AssetRemarks.objects.filter(organization=self.request.user.organization)

class AssetRemarksCreateView(LoginRequiredMixin, CreateView):
    model = AssetRemarks
    form_class = AssetRemarksForm
    template_name = 'assets/configuration/assetremarks_form.html'
    success_url = reverse_lazy('assetremarks-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class AssetRemarksUpdateView(LoginRequiredMixin, UpdateView):
    model = AssetRemarks
    form_class = AssetRemarksForm
    template_name = 'assets/configuration/assetremarks_form.html'
    success_url = reverse_lazy('assetremarks-list')
    
    def get_queryset(self):
        return AssetRemarks.objects.filter(organization=self.request.user.organization)

# AJAX endpoints for new cascading dropdowns
def get_subgroups(request):
    group_id = request.GET.get('group_id')
    if group_id:
        subgroups = SubGroup.objects.filter(group_id=group_id).values('id', 'name')
        return JsonResponse(list(subgroups), safe=False)
    return JsonResponse([], safe=False)

# ==================== APPROVAL WORKFLOW VIEWS ====================

from .models import ApprovalRequest, ApprovalLog
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import HttpResponseRedirect
from apps.users.views import ApprovalAccessMixin, CheckerRequiredMixin, SeniorManagerRequiredMixin, DataEntryRequiredMixin

class ApprovalListView(ApprovalAccessMixin, ListView):
    """List approval requests for current user"""
    model = ApprovalRequest
    template_name = 'assets/approval_list.html'
    context_object_name = 'approvals'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        # Checkers see pending requests and requests they approved
        if user.is_checker:
            return ApprovalRequest.objects.filter(
                organization=user.organization,
                status__in=[
                    ApprovalRequest.Status.PENDING,
                    ApprovalRequest.Status.CHECKER_APPROVED,
                    ApprovalRequest.Status.CHECKER_REJECTED
                ]
            ).order_by('-created_at')
        
        # Senior managers see all requests that need approval or they've already approved
        elif user.is_senior_manager:
            return ApprovalRequest.objects.filter(
                organization=user.organization,
                status__in=[
                    ApprovalRequest.Status.CHECKER_APPROVED,
                    ApprovalRequest.Status.SENIOR_APPROVED,
                    ApprovalRequest.Status.SENIOR_REJECTED,
                    ApprovalRequest.Status.APPROVED
                ]
            ).order_by('-created_at')
        
        # Data entry persons see their own requests
        elif user.is_data_entry:
            return ApprovalRequest.objects.filter(
                organization=user.organization,
                requester=user
            ).order_by('-created_at')
        
        # Admins see all
        elif user.is_superuser or user.role == user.Role.ADMIN:
            return ApprovalRequest.objects.filter(
                organization=user.organization
            ).order_by('-created_at')
        
        return ApprovalRequest.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Count pending for user's role
        queryset = self.get_queryset()
        if user.is_checker:
            context['pending_count'] = queryset.filter(status=ApprovalRequest.Status.PENDING).count()
        elif user.is_senior_manager:
            context['pending_count'] = queryset.filter(status=ApprovalRequest.Status.CHECKER_APPROVED).count()
        
        return context


class ApprovalDetailView(ApprovalAccessMixin, DetailView):
    """View approval request details"""
    model = ApprovalRequest
    template_name = 'assets/approval_detail.html'
    context_object_name = 'approval'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == user.Role.ADMIN:
            return ApprovalRequest.objects.filter(organization=user.organization)
        return ApprovalRequest.objects.filter(organization=user.organization)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approval = self.object
        context['approval_logs'] = approval.approval_logs.all().order_by('-created_at')
        context['can_approve_checker'] = self.request.user.is_checker and approval.needs_checker_approval
        context['can_approve_senior'] = self.request.user.is_senior_manager and approval.needs_senior_approval
        return context


class ApprovalApproveView(LoginRequiredMixin, View):
    """Approve an approval request"""
    
    def post(self, request, pk):
        approval = get_object_or_404(ApprovalRequest, pk=pk, organization=request.user.organization)
        user = request.user
        
        decision = request.POST.get('decision')  # 'APPROVED' or 'REJECTED'
        comments = request.POST.get('comments', '')
        
        # Checker approval
        if user.is_checker and approval.status == ApprovalRequest.Status.PENDING:
            if decision == 'APPROVED':
                approval.status = ApprovalRequest.Status.CHECKER_APPROVED
                messages.success(request, 'Request approved by checker. Pending senior manager approval.')
            elif decision == 'REJECTED':
                approval.status = ApprovalRequest.Status.CHECKER_REJECTED
                messages.warning(request, 'Request rejected by checker.')
            
            approval.save()
            
            # Create approval log
            ApprovalLog.objects.create(
                approval_request=approval,
                approver=user,
                decision=decision,
                approval_level='CHECKER',
                comments=comments,
                organization=user.organization
            )
        
        # Senior manager approval
        elif user.is_senior_manager and approval.status == ApprovalRequest.Status.CHECKER_APPROVED:
            if decision == 'APPROVED':
                approval.status = ApprovalRequest.Status.APPROVED
                messages.success(request, 'Request fully approved!')
            elif decision == 'REJECTED':
                approval.status = ApprovalRequest.Status.SENIOR_REJECTED
                messages.warning(request, 'Request rejected by senior manager.')
            
            approval.save()
            
            # Create approval log
            ApprovalLog.objects.create(
                approval_request=approval,
                approver=user,
                decision=decision,
                approval_level='SENIOR_MANAGER',
                comments=comments,
                organization=user.organization
            )
        
        else:
            messages.error(request, 'You do not have permission to approve this request.')
            return HttpResponseRedirect(reverse('approval_detail', args=[pk]))
        
        return HttpResponseRedirect(reverse('approval_detail', args=[pk]))


class CreateApprovalRequestView(DataEntryRequiredMixin, CreateView):
    """Data entry person creates approval request for new asset"""
    model = ApprovalRequest
    fields = ['request_type', 'data', 'comments']
    template_name = 'assets/approval_request_form.html'
    
    def form_valid(self, form):
        form.instance.requester = self.request.user
        form.instance.organization = self.request.user.organization
        messages.success(self.request, 'Approval request submitted for review.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('approval_list')


class ReportsListView(LoginRequiredMixin, View):
    """Display list of available reports"""
    template_name = 'assets/reports_list.html'
    
    def get(self, request):
        # Define available reports
        reports = [
            {
                'name': 'Depreciation Report',
                'description': 'View asset depreciation analysis and financial depreciation data.',
                'icon': 'trending-down',
                'url': reverse('asset-list') + '?view=depreciation',
                'color': 'info'
            },
            {
                'name': 'Asset Inventory',
                'description': 'Complete list of all assets in your inventory with details.',
                'icon': 'package',
                'url': reverse('asset-list'),
                'color': 'primary'
            },
            {
                'name': 'Asset Approvals',
                'description': 'View and manage pending and completed asset approval requests.',
                'icon': 'check-circle',
                'url': reverse('approval_list'),
                'color': 'success'
            },
        ]
        
        context = {
            'reports': reports,
            'total_assets': Asset.objects.filter(
                organization=request.user.organization
            ).count(),
        }
        
        return render(request, self.template_name, context)


class MastersListView(LoginRequiredMixin, View):
    """Display list of all assets with complete details - with pagination and filters"""
    template_name = 'assets/masters_list.html'
    paginate_by = 50
    
    def get(self, request):
        from django.core.paginator import Paginator
        from django.db.models import Q
        organization = request.user.organization
        
        # Get search and filter parameters
        search_query = request.GET.get('q', '').strip()
        category_filter = request.GET.get('category', '').strip()
        sub_category_filter = request.GET.get('sub_category', '').strip()
        company_filter = request.GET.get('company', '').strip()
        department_filter = request.GET.get('department', '').strip()
        condition_filter = request.GET.get('condition', '').strip()
        status_filter = request.GET.get('status', '').strip()
        brand_filter = request.GET.get('brand', '').strip()
        vendor_filter = request.GET.get('vendor', '').strip()
        supplier_filter = request.GET.get('supplier', '').strip()
        group_filter = request.GET.get('group', '').strip()
        subgroup_filter = request.GET.get('subgroup', '').strip()
        custodian_filter = request.GET.get('custodian', '').strip()
        purchase_date_from = request.GET.get('purchase_date_from', '').strip()
        purchase_date_to = request.GET.get('purchase_date_to', '').strip()
        sort_by = request.GET.get('sort_by', '-created_at').strip()
        sort_order = request.GET.get('sort_order', 'desc').strip()
        
        # Fetch assets with optimization
        assets_qs = Asset.objects.filter(
            organization=organization
        ).select_related(
            'category', 'sub_category', 'group', 'sub_group', 'brand_new',
            'company', 'supplier', 'custodian', 'department', 'assigned_to',
            'branch', 'building', 'floor', 'room', 'region', 'site', 
            'location', 'sub_location', 'vendor', 'asset_remarks', 'parent'
        )
        
        # Apply sorting
        if sort_by:
            if sort_order == 'asc':
                assets_qs = assets_qs.order_by(sort_by)
            else:
                assets_qs = assets_qs.order_by(f'-{sort_by}' if not sort_by.startswith('-') else sort_by)
        else:
            assets_qs = assets_qs.order_by('-created_at')
        
        # Apply search filter
        if search_query:
            assets_qs = assets_qs.filter(
                Q(asset_tag__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(serial_number__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Apply category and sub-category filters
        if category_filter:
            assets_qs = assets_qs.filter(category_id=category_filter)
        if sub_category_filter:
            assets_qs = assets_qs.filter(sub_category_id=sub_category_filter)
        
        # Apply company filter
        if company_filter:
            assets_qs = assets_qs.filter(company_id=company_filter)
        
        # Apply department filter
        if department_filter:
            assets_qs = assets_qs.filter(department_id=department_filter)
        
        # Apply condition filter
        if condition_filter:
            assets_qs = assets_qs.filter(condition=condition_filter)
        
        # Apply status filter
        if status_filter:
            assets_qs = assets_qs.filter(status=status_filter)
        
        # Apply brand filter
        if brand_filter:
            assets_qs = assets_qs.filter(brand_new_id=brand_filter)
        
        # Apply vendor filter
        if vendor_filter:
            assets_qs = assets_qs.filter(vendor_id=vendor_filter)
        
        # Apply supplier filter
        if supplier_filter:
            assets_qs = assets_qs.filter(supplier_id=supplier_filter)
        
        # Apply group filter
        if group_filter:
            assets_qs = assets_qs.filter(group_id=group_filter)
        
        # Apply subgroup filter
        if subgroup_filter:
            assets_qs = assets_qs.filter(sub_group_id=subgroup_filter)
        
        # Apply custodian filter
        if custodian_filter:
            assets_qs = assets_qs.filter(custodian_id=custodian_filter)
        
        # Apply purchase date range filters
        if purchase_date_from:
            try:
                from datetime import datetime
                from_date = datetime.strptime(purchase_date_from, '%Y-%m-%d').date()
                assets_qs = assets_qs.filter(purchase_date__gte=from_date)
            except:
                pass
        
        if purchase_date_to:
            try:
                from datetime import datetime
                to_date = datetime.strptime(purchase_date_to, '%Y-%m-%d').date()
                assets_qs = assets_qs.filter(purchase_date__lte=to_date)
            except:
                pass
        
        # Paginate results
        paginator = Paginator(assets_qs, self.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get filter options
        categories = Category.objects.filter(organization=organization).order_by('name')
        sub_categories = SubCategory.objects.filter(organization=organization).order_by('name')
        companies = Company.objects.filter(organization=organization).order_by('name')
        departments = Department.objects.filter(organization=organization).order_by('name')
        brands = Brand.objects.filter(organization=organization).order_by('name')
        vendors = Vendor.objects.filter(organization=organization).order_by('name')
        suppliers = Supplier.objects.filter(organization=organization).order_by('name')
        groups = Group.objects.filter(organization=organization).order_by('name')
        subgroups = SubGroup.objects.filter(organization=organization).order_by('name')
        custodians = Custodian.objects.filter(organization=organization).order_by('employee_id')
        
        context = {
            'page_obj': page_obj,
            'assets': page_obj.object_list,
            'total_assets': paginator.count,
            'search_query': search_query,
            'category_filter': category_filter,
            'sub_category_filter': sub_category_filter,
            'company_filter': company_filter,
            'department_filter': department_filter,
            'condition_filter': condition_filter,
            'status_filter': status_filter,
            'brand_filter': brand_filter,
            'vendor_filter': vendor_filter,
            'supplier_filter': supplier_filter,
            'group_filter': group_filter,
            'subgroup_filter': subgroup_filter,
            'custodian_filter': custodian_filter,
            'purchase_date_from': purchase_date_from,
            'purchase_date_to': purchase_date_to,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'categories': categories,
            'sub_categories': sub_categories,
            'companies': companies,
            'departments': departments,
            'brands': brands,
            'vendors': vendors,
            'suppliers': suppliers,
            'groups': groups,
            'subgroups': subgroups,
            'custodians': custodians,
            'condition_choices': Asset._meta.get_field('condition').choices,
            'status_choices': Asset._meta.get_field('status').choices,
        }
        
        return render(request, self.template_name, context)


# ========================
# Asset Transfer Views
# ========================

class AssetTransferListView(LoginRequiredMixin, ListView):
    """List all asset transfers with filtering"""
    model = AssetTransfer
    template_name = 'assets/transfer_list.html'
    context_object_name = 'transfers'
    paginate_by = 50
    
    def get_queryset(self):
        org = self.request.user.organization
        queryset = AssetTransfer.objects.filter(organization=org).select_related(
            'asset',
            'transferred_from_user',
            'transferred_from_department',
            'transferred_to_user',
            'transferred_to_department',
            'created_by'
        )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by asset
        asset_id = self.request.GET.get('asset')
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(transfer_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transfer_date__lte=date_to)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset__asset_tag__icontains=search) |
                Q(asset__name__icontains=search) |
                Q(transfer_reason__icontains=search)
            )
        
        return queryset.order_by('-transfer_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        
        context['status_choices'] = AssetTransfer.Status.choices
        context['assets'] = Asset.objects.filter(organization=org)
        context['status_filter'] = self.request.GET.get('status', '')
        context['asset_filter'] = self.request.GET.get('asset', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['search'] = self.request.GET.get('search', '')
        
        return context


class AssetTransferCreateView(LoginRequiredMixin, CreateView):
    """Create a new asset transfer"""
    model = AssetTransfer
    form_class = AssetTransferForm
    template_name = 'assets/transfer_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Asset transfer created successfully for {form.instance.asset.asset_tag}')
        return response
    
    def get_success_url(self):
        return reverse('transfer-detail', kwargs={'pk': self.object.pk})


class AssetTransferDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific asset transfer"""
    model = AssetTransfer
    template_name = 'assets/transfer_detail.html'
    context_object_name = 'transfer'
    
    def get_queryset(self):
        org = self.request.user.organization
        return AssetTransfer.objects.filter(organization=org).select_related(
            'asset',
            'transferred_from_user',
            'transferred_from_department',
            'transferred_from_location',
            'transferred_to_user',
            'transferred_to_department',
            'transferred_to_location',
            'created_by',
            'received_by'
        )


class AssetTransferUpdateView(LoginRequiredMixin, UpdateView):
    """Update an asset transfer (mainly for status changes)"""
    model = AssetTransfer
    form_class = AssetTransferForm
    template_name = 'assets/transfer_form.html'
    
    def get_queryset(self):
        org = self.request.user.organization
        return AssetTransfer.objects.filter(organization=org)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Asset transfer updated successfully')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('transfer-detail', kwargs={'pk': self.object.pk})


class AssetTransferReceiveView(LoginRequiredMixin, UpdateView):
    """Mark an asset transfer as received"""
    model = AssetTransfer
    form_class = AssetTransferReceiveForm
    template_name = 'assets/transfer_receive.html'
    
    def get_queryset(self):
        org = self.request.user.organization
        return AssetTransfer.objects.filter(organization=org)
    
    def form_valid(self, form):
        form.instance.received_by = self.request.user
        if form.instance.status == AssetTransfer.Status.RECEIVED:
            if not form.instance.actual_receipt_date:
                form.instance.actual_receipt_date = date.today()
            messages.success(self.request, f'Asset transfer marked as received: {form.instance.asset.asset_tag}')
        elif form.instance.status == AssetTransfer.Status.REJECTED:
            messages.warning(self.request, f'Asset transfer rejected: {form.instance.asset.asset_tag}')
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('transfer-detail', kwargs={'pk': self.object.pk})