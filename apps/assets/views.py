from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, FormView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.contrib import messages
import csv
import io
from .models import (Asset, AssetAttachment, Category, SubCategory, Vendor, generate_asset_tag,
                     Group, SubGroup, Brand, Company, Supplier, Custodian, AssetRemarks, AssetTransfer, AssetDisposal)
from .forms import (AssetForm, CategoryForm, SubCategoryForm, VendorForm, AssetImportForm,
                    GroupForm, SubGroupForm, BrandForm, CompanyForm, SupplierForm, CustodianForm, AssetRemarksForm, AssetTransferForm, AssetTransferReceiveForm, AssetDisposalForm, AssetDisposalManagerApprovalForm, AssetDisposalApprovalForm)
from django.db import transaction, models
from apps.locations.models import (Branch, Building, Floor, Room, 
                                   Region, Site, Location, SubLocation, Department)
from django.urls import reverse
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from decimal import Decimal
from datetime import date, datetime
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from uuid import uuid4
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


def get_buildings_by_site(request):
    """Return buildings associated with a given site (via Location->building link)."""
    site_id = request.GET.get('site_id')
    if site_id:
        buildings = Building.objects.filter(locations__site_id=site_id).distinct().values('id', 'name')
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

def get_locations(request):
    """Return locations filtered by building_id (optional)."""
    building_id = request.GET.get('building_id')
    if building_id:
        locations = Location.objects.filter(building_id=building_id).values('id', 'name')
        return JsonResponse(list(locations), safe=False)
    return JsonResponse([], safe=False)

def lookup_asset(request):
    # Support lookup by free-text `q` (tag/name/code), `asset_tag`, or by explicit `asset_id`.
    asset_id = request.GET.get('asset_id')
    query = request.GET.get('q')
    asset_tag = request.GET.get('asset_tag')

    asset = None
    org = getattr(request.user, 'organization', None)

    if asset_id:
        try:
            asset = Asset.objects.select_related(
                'department', 'branch', 'building', 'floor', 'room',
                'region', 'site', 'location', 'sub_location', 'assigned_to',
                'company', 'custodian'
            ).get(id=asset_id, organization=org)
        except Asset.DoesNotExist:
            asset = None

    elif asset_tag:
        # Search by asset tag
        asset = Asset.objects.filter(
            Q(asset_tag__iexact=asset_tag),
            organization=org
        ).select_related(
            'department', 'branch', 'building', 'floor', 'room',
            'region', 'site', 'location', 'sub_location', 'assigned_to',
            'company', 'custodian'
        ).first()

    elif query:
        # Prioritize exact match on tags, then partial on name
        asset = Asset.objects.filter(
            Q(asset_tag__iexact=query) | 
            Q(asset_code__iexact=query),
            organization=org
        ).select_related(
            'department', 'branch', 'building', 'floor', 'room',
            'region', 'site', 'location', 'sub_location', 'assigned_to',
            'company', 'custodian'
        ).first()

        if not asset:
            # Fallback to name search if no exact tag match
            asset = Asset.objects.filter(
                name__icontains=query,
                organization=org
            ).select_related(
                'department', 'branch', 'building', 'floor', 'room',
                'region', 'site', 'location', 'sub_location', 'assigned_to',
                'company', 'custodian'
            ).first()

    if not asset:
        return JsonResponse({'error': 'Not found'}, status=404)

    # Current location/ownership details
    assigned = None
    if asset.assigned_to:
        assigned = {'id': asset.assigned_to.id, 'name': asset.assigned_to.get_full_name() or asset.assigned_to.username}

    company = None
    if hasattr(asset, 'company') and asset.company:
        company = {'id': asset.company.id, 'name': asset.company.name}

    custodian = None
    if hasattr(asset, 'custodian') and asset.custodian:
        custodian = {'id': asset.custodian.id, 'name': asset.custodian.name}

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
        'company': company,
        'custodian': custodian,
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
    'name', 'description', 'short_description',
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
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Assets"

    # Style definitions
    header_font = Font(name='Calibri', bold=True, size=11, color='FFFFFF')
    header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    data_font = Font(name='Calibri', size=11)
    data_alignment = Alignment(horizontal='left', vertical='center', wrap_text=False)
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9'),
    )
    alt_row_fill = PatternFill(start_color='F2F7FB', end_color='F2F7FB', fill_type='solid')

    # Header row
    ws.append(ASSET_IMPORT_FIELDS)

    # Sample row
    sample_data = [
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
    ]
    ws.append(sample_data)

    # Apply header styles
    for col_idx, header in enumerate(ASSET_IMPORT_FIELDS, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Apply data row styles
    for col_idx in range(1, len(ASSET_IMPORT_FIELDS) + 1):
        cell = ws.cell(row=2, column=col_idx)
        cell.font = data_font
        cell.alignment = data_alignment
        cell.border = thin_border
        cell.fill = alt_row_fill

    # Auto-fit column widths based on content
    for col_idx, header in enumerate(ASSET_IMPORT_FIELDS, 1):
        col_letter = get_column_letter(col_idx)
        header_len = len(str(header))
        data_val = sample_data[col_idx - 1] if col_idx - 1 < len(sample_data) else ''
        data_len = len(str(data_val))
        optimal_width = max(header_len, data_len) + 4
        optimal_width = min(optimal_width, 40)
        optimal_width = max(optimal_width, 12)
        ws.column_dimensions[col_letter].width = optimal_width

    # Set row heights
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 22

    # Freeze header row
    ws.freeze_panes = 'A2'

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

    def get(self, request, *args, **kwargs):
        if request.GET.get('view') == 'depreciation':
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(reverse('depreciation-report'))
        return super().get(request, *args, **kwargs)

    def get_template_names(self):
        return ['assets/asset_list.html']

    def get_queryset(self):
        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False
        ).select_related(
            'category', 'sub_category', 'branch', 'assigned_to', 
            'site', 'building', 'brand_new', 'room', 'department',
            'sub_location', 'group'
        ).prefetch_related('attachments')

        # Search across many asset fields and common related names
        query = self.request.GET.get('q')
        if query:
            q = (
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
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
        user = self.request.user
        
        # Determine if financial data should be shown - for CHECKER and above roles
        show_financial = user.role in [user.Role.CHECKER, user.Role.SENIOR_MANAGER, user.Role.ADMIN] or user.is_superuser
        context['show_financial'] = show_financial
        
        # Calculate total values for filtered assets
        if show_financial:
            from django.db.models import Sum, Count
            from django.db.models.functions import Coalesce
            
            filtered_queryset = self.get_queryset()
            
            # Calculate aggregates
            aggregates = filtered_queryset.aggregate(
                total_purchase_value=Coalesce(Sum('purchase_price'), Decimal('0')),
                total_asset_count=Count('id')
            )
            
            context['total_purchase_value'] = aggregates['total_purchase_value']
            context['filtered_asset_count'] = aggregates['total_asset_count']
            
            # Calculate current value (NBV) for filtered assets
            # For performance, only calculate if there are reasonable number of assets
            if aggregates['total_asset_count'] <= 1000:
                # Direct calculation for small datasets
                filtered_assets = list(filtered_queryset)
                total_current_value = sum(asset.current_value for asset in filtered_assets if hasattr(asset, 'current_value'))
                total_accumulated_depreciation = sum(asset.accumulated_depreciation for asset in filtered_assets if hasattr(asset, 'accumulated_depreciation'))
            else:
                # Estimate for large datasets
                sample_size = 500
                sample_assets = list(filtered_queryset[:sample_size])
                if sample_assets:
                    avg_depreciation_ratio = sum(asset.accumulated_depreciation for asset in sample_assets) / sum(asset.purchase_price or Decimal('0') for asset in sample_assets if asset.purchase_price) if any(asset.purchase_price for asset in sample_assets) else 0
                    total_accumulated_depreciation = aggregates['total_purchase_value'] * Decimal(str(avg_depreciation_ratio))
                    total_current_value = aggregates['total_purchase_value'] - total_accumulated_depreciation
                else:
                    total_accumulated_depreciation = Decimal('0')
                    total_current_value = aggregates['total_purchase_value']
            
            context['total_current_value'] = total_current_value
            context['total_accumulated_depreciation'] = total_accumulated_depreciation
            
            # Pass date filter values to context
            context['purchase_date_from'] = self.request.GET.get('purchase_date_from', '')
            context['purchase_date_to'] = self.request.GET.get('purchase_date_to', '')
        
        # Use only() to reduce database load for filter dropdowns
        context['categories'] = Category.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['sites'] = Site.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['buildings'] = Building.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['brands'] = Brand.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['departments'] = Department.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['subcategories'] = SubCategory.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['groups'] = Group.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['branches'] = Branch.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['locations'] = Location.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['statuses'] = Asset.Status.choices

        if self.request.GET.get('view') == 'depreciation' and show_financial:
            # Depreciation report with efficient aggregation
            from django.db.models import Sum, Count, Q
            from django.db.models.functions import Coalesce
            from datetime import datetime
            
            queryset = self.get_queryset()
            
            # CRITICAL: Only show assets with purchase price (exclude assets without value)
            queryset = queryset.filter(purchase_price__isnull=False, purchase_price__gt=0)
            
            # Add date filtering for depreciation report
            depr_date_from = self.request.GET.get('depr_date_from')
            depr_date_to = self.request.GET.get('depr_date_to')
            
            opening_date = None
            closing_date = None
            
            if depr_date_from:
                try:
                    opening_date = datetime.strptime(depr_date_from, '%Y-%m-%d').date()
                    # Don't filter by purchase date, we want all assets that existed at opening date
                except (ValueError, TypeError):
                    pass
            
            if depr_date_to:
                try:
                    closing_date = datetime.strptime(depr_date_to, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass
            
            # Filter to only show assets purchased on or before the closing date (if provided)
            if closing_date:
                queryset = queryset.filter(Q(purchase_date__lte=closing_date) | Q(purchase_date__isnull=True))
            
            # Add location and category filters for depreciation report
            depr_filters = {
                'depr_category': 'category_id',
                'depr_group': 'group_id',
                'depr_department': 'department_id',
                'depr_site': 'site_id',
                'depr_branch': 'branch_id',
                'depr_building': 'building_id',
                'depr_location': 'location_id',
            }
            
            for param, field in depr_filters.items():
                val = self.request.GET.get(param)
                if val:
                    queryset = queryset.filter(**{field: val})
                    context[param] = val
            
            # Use database aggregation directly for efficiency
            # Only aggregate purchase_price (a database field)
            agg = queryset.aggregate(
                total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
                total_count=Count('id')
            )
            
            total_cost = agg['total_cost']
            total_count = agg['total_count']
            
            # Calculate opening and closing values
            total_opening_value = Decimal('0')
            total_closing_value = Decimal('0')
            
            # Calculate exact values by iterating all assets in batches
            # This matches the dashboard calculation for consistency
            BATCH_SIZE = 1000
            
            total_acc_dep = Decimal('0')
            total_nbv = Decimal('0')
            
            if opening_date or closing_date:
                # Need to calculate period-based values
                for i in range(0, total_count, BATCH_SIZE):
                    batch = list(queryset[i:i+BATCH_SIZE])
                    for asset in batch:
                        if opening_date:
                            total_opening_value += asset.get_value_at_date(opening_date)
                        else:
                            total_opening_value += asset.current_value
                        
                        if closing_date:
                            total_closing_value += asset.get_value_at_date(closing_date)
                        else:
                            total_closing_value += asset.current_value
                        
                        total_acc_dep += asset.accumulated_depreciation
                
                total_nbv = total_closing_value
            else:
                # No date range - just compute current values
                for i in range(0, total_count, BATCH_SIZE):
                    batch = list(queryset[i:i+BATCH_SIZE])
                    for asset in batch:
                        cv = asset.current_value
                        total_nbv += cv
                        total_acc_dep += asset.accumulated_depreciation
                
                total_opening_value = total_nbv
                total_closing_value = total_nbv
            
            # Calculate depreciation for the period
            period_depreciation = total_opening_value - total_closing_value
            
            context['total_cost'] = total_cost
            context['total_opening_value'] = total_opening_value
            context['total_closing_value'] = total_closing_value
            context['period_depreciation'] = period_depreciation
            context['total_acc_dep'] = total_acc_dep
            context['total_nbv'] = total_nbv
            context['is_report'] = True
            context['total_assets_report'] = total_count
            context['depr_date_from'] = depr_date_from
            context['depr_date_to'] = depr_date_to
            context['opening_date'] = opening_date
            context['closing_date'] = closing_date
            
            # Support grouped summaries
            group_by = self.request.GET.get('group_by')
            context['group_by'] = group_by
            
            if group_by == 'category':
                # Efficient category grouping without loading all assets
                grouped_data = queryset.values('category', 'category__name').annotate(
                    count=Count('id'),
                    total_cost=Sum('purchase_price')
                ).order_by('-total_cost')[:100]  # Limit to top 100 categories
                
                # Calculate exact depreciation for each category
                grouped_list = []
                for group in grouped_data:
                    cat_id = group['category']
                    cat_qs = queryset.filter(category_id=cat_id)
                    
                    cat_assets = list(cat_qs)
                    total_cat_dep = sum(a.accumulated_depreciation for a in cat_assets) if cat_assets else Decimal('0')
                    
                    grouped_list.append({
                        'id': cat_id,
                        'name': group['category__name'] or 'Uncategorized',
                        'total_cost': group['total_cost'] or Decimal('0'),
                        'total_acc_dep': total_cat_dep,
                        'total_nbv': (group['total_cost'] or Decimal('0')) - total_cat_dep,
                        'count': group['count'],
                    })
                context['grouped_data'] = grouped_list
            
            # Paginate the filtered depreciation assets
            from django.core.paginator import Paginator
            paginator = Paginator(queryset, 25)  # 25 items per page
            page_number = self.request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Add opening and closing values to each asset
            assets_with_values = []
            for asset in page_obj.object_list:
                asset_dict = asset
                if opening_date:
                    asset_dict.opening_value = asset.get_value_at_date(opening_date)
                else:
                    asset_dict.opening_value = asset.current_value
                
                if closing_date:
                    asset_dict.closing_value = asset.get_value_at_date(closing_date)
                else:
                    asset_dict.closing_value = asset.current_value
                
                asset_dict.period_depreciation = asset_dict.opening_value - asset_dict.closing_value
                assets_with_values.append(asset_dict)
            
            context['assets'] = assets_with_values
            context['page_obj'] = page_obj
            context['is_paginated'] = page_obj.has_other_pages()
        
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
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        # We reuse the logic from AssetListView to respect current filters
        view = AssetListView()
        view.request = request
        queryset = view.get_queryset().select_related(
            'category', 'sub_category', 'group', 'sub_group', 'brand_new',
            'company', 'supplier', 'custodian', 'department', 'assigned_to',
            'branch', 'building', 'floor', 'room', 'region', 'site',
            'location', 'sub_location', 'vendor', 'asset_remarks', 'parent'
        )

        is_depreciation_view = request.GET.get('view') == 'depreciation'

        opening_date = None
        closing_date = None

        if is_depreciation_view:
            queryset = queryset.filter(purchase_price__isnull=False, purchase_price__gt=0)

            depr_filters = {
                'depr_category': 'category_id',
                'depr_group': 'group_id',
                'depr_department': 'department_id',
                'depr_site': 'site_id',
                'depr_branch': 'branch_id',
                'depr_building': 'building_id',
                'depr_location': 'location_id',
            }

            for param, field in depr_filters.items():
                val = request.GET.get(param)
                if val:
                    queryset = queryset.filter(**{field: val})

            depr_date_from = request.GET.get('depr_date_from')
            depr_date_to = request.GET.get('depr_date_to')

            if depr_date_from:
                try:
                    opening_date = datetime.strptime(depr_date_from, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    opening_date = None

            if depr_date_to:
                try:
                    closing_date = datetime.strptime(depr_date_to, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    closing_date = None

            if closing_date:
                queryset = queryset.filter(Q(purchase_date__lte=closing_date) | Q(purchase_date__isnull=True))

        wb = openpyxl.Workbook()
        ws = wb.active

        # ── Styles ──
        title_font = Font(size=14, bold=True, color="1F4E79")
        meta_label_font = Font(bold=True, size=10, color="1F4E79")
        meta_value_font = Font(size=10)
        header_font = Font(bold=True, color="FFFFFF", size=10)
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        even_fill = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin', color='B0B0B0'),
            right=Side(style='thin', color='B0B0B0'),
            top=Side(style='thin', color='B0B0B0'),
            bottom=Side(style='thin', color='B0B0B0'),
        )
        currency_format = '#,##0.00'
        date_format = 'YYYY-MM-DD'

        if is_depreciation_view:
            ws.title = "Depreciation Export"

            # ── Title block ──
            current_row = 1
            ws.merge_cells('A1:G1')
            cell = ws.cell(row=1, column=1, value="DEPRECIATION REPORT EXPORT")
            cell.font = title_font
            cell.alignment = Alignment(horizontal='left', vertical='center')
            current_row = 2

            ws.cell(row=current_row, column=1, value="Export Date:").font = meta_label_font
            ws.cell(row=current_row, column=2, value=datetime.now().strftime("%Y-%m-%d %H:%M")).font = meta_value_font
            current_row += 1
            ws.cell(row=current_row, column=1, value="Total Records:").font = meta_label_font
            ws.cell(row=current_row, column=2, value=queryset.count()).font = meta_value_font
            current_row += 2

            headers = [
                'Asset Tag', 'Asset Code', 'Name', 'Category', 'Status',
                'Purchase Date', 'Purchase Price', 'Currency',
            ]
            if opening_date:
                headers.append(f'Opening Value ({opening_date.strftime("%Y-%m-%d")})')
            if closing_date:
                headers.append(f'Closing Value ({closing_date.strftime("%Y-%m-%d")})')
            if opening_date and closing_date:
                headers.append('Period Depreciation')
            headers.extend(['Accumulated Depreciation', 'Current NBV'])

            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=current_row, column=col_num, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = thin_border
            current_row += 1

            data_start = current_row
            for asset in queryset:
                opening_value = asset.get_value_at_date(opening_date) if opening_date else asset.current_value
                closing_value = asset.get_value_at_date(closing_date) if closing_date else asset.current_value
                if opening_date and opening_value <= 0:
                    continue

                row = [
                    asset.asset_tag,
                    asset.asset_code or '',
                    asset.name,
                    asset.category.name if asset.category else '',
                    asset.get_status_display(),
                    asset.purchase_date,
                    float(asset.purchase_price) if asset.purchase_price else 0,
                    asset.currency,
                ]
                if opening_date:
                    row.append(float(opening_value))
                if closing_date:
                    row.append(float(closing_value))
                if opening_date and closing_date:
                    row.append(float(opening_value - closing_value))
                row.extend([float(asset.accumulated_depreciation), float(asset.current_value)])

                for col_num, value in enumerate(row, 1):
                    cell = ws.cell(row=current_row, column=col_num, value=value)
                    cell.border = thin_border
                    if isinstance(value, float):
                        cell.number_format = currency_format
                if (current_row - data_start) % 2 == 0:
                    for col_num in range(1, len(row) + 1):
                        ws.cell(row=current_row, column=col_num).fill = even_fill
                current_row += 1

        else:
            ws.title = "Assets Export"

            # ── Title block ──
            current_row = 1
            ws.merge_cells('A1:H1')
            cell = ws.cell(row=1, column=1, value="ASSET INVENTORY EXPORT")
            cell.font = title_font
            cell.alignment = Alignment(horizontal='left', vertical='center')
            current_row = 2

            ws.cell(row=current_row, column=1, value="Export Date:").font = meta_label_font
            ws.cell(row=current_row, column=2, value=datetime.now().strftime("%Y-%m-%d %H:%M")).font = meta_value_font
            current_row += 1
            ws.cell(row=current_row, column=1, value="Total Records:").font = meta_label_font
            ws.cell(row=current_row, column=2, value=queryset.count()).font = meta_value_font
            current_row += 1

            # Show active filters
            filters_applied = []
            q = request.GET.get('q', '').strip()
            if q:
                filters_applied.append(f"Search: {q}")
            for param, label in [('status', 'Status'), ('category', 'Category'), ('site', 'Site'),
                                 ('building', 'Building'), ('brand', 'Brand'), ('department', 'Department'),
                                 ('subcategory', 'Sub Category'), ('group', 'Group')]:
                val = request.GET.get(param, '').strip()
                if val:
                    filters_applied.append(f"{label}: {val}")
            if filters_applied:
                current_row += 1
                ws.cell(row=current_row, column=1, value="Applied Filters:").font = meta_label_font
                current_row += 1
                for ft in filters_applied:
                    ws.cell(row=current_row, column=1, value=f"  • {ft}").font = meta_value_font
                    current_row += 1

            current_row += 1  # blank row before data

            # ── ALL column headers ──
            headers = [
                # Identification
                'Asset Tag', 'Asset Code', 'ERP Asset Number', 'Name', 'Short Description', 'Description',
                'Serial Number', 'Quantity', 'Label Type', 'Asset Type',
                # Classification
                'Category', 'Sub Category', 'Group', 'Sub Group', 'Brand', 'Model', 'Condition',
                # Ownership
                'Company', 'Department', 'Assigned To', 'Custodian', 'Employee Number',
                'Cost Center', 'Supplier', 'Vendor',
                # Location
                'Region', 'Site', 'Branch', 'Building', 'Floor', 'Room',
                'Location', 'Sub Location',
                # Financial
                'Purchase Date', 'Purchase Price', 'Currency', 'Invoice Number', 'Invoice Date',
                'PO Number', 'PO Date', 'DO Number', 'DO Date', 'GRN Number',
                'Warranty Start', 'Warranty End',
                # Depreciation
                'Depreciation Method', 'Useful Life (Years)', 'Salvage Value',
                'Accumulated Depreciation', 'Current NBV',
                # Dates
                'Date Placed in Service', 'Tagged Date',
                'Insurance Start', 'Insurance End',
                'Maintenance Start', 'Maintenance End',
                'Maintenance Frequency (Days)', 'Next Maintenance Date',
                # Other
                'Status', 'Parent Asset', 'Remarks / Notes',
                'Created At',
            ]

            header_row_num = current_row
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=current_row, column=col_num, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = thin_border
            current_row += 1

            # Freeze the header row so it stays visible while scrolling
            ws.freeze_panes = ws.cell(row=current_row, column=1)

            # ── Data rows ──
            data_start = current_row
            for asset in queryset:
                row_data = [
                    # Identification
                    asset.asset_tag or '',
                    asset.asset_code or '',
                    asset.erp_asset_number or '',
                    asset.name or '',
                    asset.short_description or '',
                    asset.description or '',
                    asset.serial_number or '',
                    asset.quantity,
                    asset.get_label_type_display() if asset.label_type else '',
                    asset.get_asset_type_display() if asset.asset_type else '',
                    # Classification
                    asset.category.name if asset.category else '',
                    asset.sub_category.name if asset.sub_category else '',
                    asset.group.name if asset.group else '',
                    asset.sub_group.name if asset.sub_group else '',
                    asset.brand_new.name if asset.brand_new else (asset.brand or ''),
                    asset.model or '',
                    asset.get_condition_display() if asset.condition else '',
                    # Ownership
                    asset.company.name if asset.company else '',
                    asset.department.name if asset.department else '',
                    asset.assigned_to.get_full_name() if asset.assigned_to else '',
                    (asset.custodian.user.get_full_name() if asset.custodian and asset.custodian.user
                     else (asset.custodian.employee_id if asset.custodian else '')),
                    asset.employee_number or '',
                    asset.cost_center or '',
                    asset.supplier.name if asset.supplier else '',
                    asset.vendor.name if asset.vendor else '',
                    # Location
                    asset.region.name if asset.region else '',
                    asset.site.name if asset.site else '',
                    asset.branch.name if asset.branch else '',
                    asset.building.name if asset.building else '',
                    asset.floor.name if asset.floor else '',
                    asset.room.name if asset.room else '',
                    asset.location.name if asset.location else '',
                    asset.sub_location.name if asset.sub_location else '',
                    # Financial
                    asset.purchase_date,
                    float(asset.purchase_price) if asset.purchase_price else '',
                    asset.currency or '',
                    asset.invoice_number or '',
                    asset.invoice_date,
                    asset.po_number or '',
                    asset.po_date,
                    asset.do_number or '',
                    asset.do_date,
                    asset.grn_number or '',
                    asset.warranty_start,
                    asset.warranty_end,
                    # Depreciation
                    asset.get_depreciation_method_display() if asset.depreciation_method else '',
                    asset.useful_life_years or '',
                    float(asset.salvage_value) if asset.salvage_value else '',
                    float(asset.accumulated_depreciation),
                    float(asset.current_value),
                    # Dates
                    asset.date_placed_in_service,
                    asset.tagged_date,
                    asset.insurance_start_date,
                    asset.insurance_end_date,
                    asset.maintenance_start_date,
                    asset.maintenance_end_date,
                    asset.maintenance_frequency_days or '',
                    asset.next_maintenance_date,
                    # Other
                    asset.get_status_display() if asset.status else '',
                    str(asset.parent) if asset.parent else '',
                    asset.notes or (asset.asset_remarks.name if asset.asset_remarks else ''),
                    asset.created_at.strftime('%Y-%m-%d %H:%M') if asset.created_at else '',
                ]

                is_even = (current_row - data_start) % 2 == 0
                for col_num, value in enumerate(row_data, 1):
                    cell = ws.cell(row=current_row, column=col_num, value=value)
                    cell.border = thin_border
                    if isinstance(value, float):
                        cell.number_format = currency_format
                    if is_even:
                        cell.fill = even_fill
                current_row += 1

        # ── Auto-adjust column widths ──
        for col_idx in range(1, ws.max_column + 1):
            max_length = 0
            for row_idx in range(1, ws.max_row + 1):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if cell_value is not None:
                    cell_length = len(str(cell_value))
                    if cell_length > max_length:
                        max_length = cell_length
            adjusted_width = min(max_length + 3, 40) if max_length > 0 else 12
            ws.column_dimensions[get_column_letter(col_idx)].width = adjusted_width

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        file_prefix = 'depreciation_export' if is_depreciation_view else 'assets_export'
        response['Content-Disposition'] = f'attachment; filename="{file_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
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
        user = self.request.user

        # Data Entry users submit for approval instead of direct inventory creation
        if getattr(user, 'role', None) == user.Role.EMPLOYEE:
            approval_data = self._build_approval_payload(form)
            ApprovalRequest.objects.create(
                organization=user.organization,
                requester=user,
                request_type=ApprovalRequest.RequestType.ASSET_CREATE,
                status=ApprovalRequest.Status.PENDING,
                data=approval_data,
                comments='Asset uploaded by employee and waiting for checker approval.'
            )
            messages.success(
                self.request,
                'Asset upload submitted for checker approval. It will be added to inventory after approval.'
            )
            return redirect('approval_list')

        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        
        # Handle bulk creation based on quantity
        quantity = form.instance.quantity if form.instance.quantity else 1
        
        if quantity > 1:
            # Create multiple assets with different auto-generated tags
            # Set quantity to 1 for each individual asset
            original_quantity = form.instance.quantity
            form.instance.quantity = 1
            
            # Create first asset with form data and auto-generated tag
            if not form.instance.asset_tag:
                form.instance.asset_tag = generate_asset_tag(
                    self.request.user.organization,
                    form.instance.category,
                    form.instance.company
                )
            
            response = super().form_valid(form)
            first_asset = form.instance
            
            # Create remaining assets one by one with their own generated tags
            # This ensures each call to generate_asset_tag sees the previously created assets
            for i in range(1, original_quantity):
                # Clone the first saved instance
                new_asset = Asset.objects.get(pk=first_asset.pk)
                new_asset.pk = None  # Clear primary key to create new record
                new_asset.id = None  # Clear UUID
                
                # Generate new tag for this asset
                new_asset.asset_tag = generate_asset_tag(
                    self.request.user.organization,
                    form.instance.category,
                    form.instance.company
                )
                new_asset.save()
            
            return response
        else:
            # Single asset creation with auto-generated tag if not provided
            if not form.instance.asset_tag:
                form.instance.asset_tag = generate_asset_tag(
                    self.request.user.organization,
                    form.instance.category,
                    form.instance.company
                )
            return super().form_valid(form)

    def _build_approval_payload(self, form):
        """Serialize asset form data for deferred creation after checker approval."""
        from django.db import models

        cleaned_data = form.cleaned_data
        payload = {}
        file_fields = {}

        model_fields = {
            field.name: field
            for field in Asset._meta.get_fields()
            if isinstance(field, models.Field)
        }
        excluded_fields = {
            'id', 'organization', 'created_by', 'asset_tag', 'custom_fields',
            'is_deleted', 'deleted_at', 'created_at', 'updated_at'
        }

        # Only serialize fields that are actually submitted in the form
        for field_name, value in cleaned_data.items():
            field = model_fields.get(field_name)
            if not field:
                continue
            if field.auto_created or field_name in excluded_fields:
                continue

            if isinstance(field, models.FileField):
                uploaded = self.request.FILES.get(field_name)
                if uploaded:
                    saved_name = default_storage.save(
                        f"approval_uploads/{uuid4()}_{uploaded.name}",
                        ContentFile(uploaded.read())
                    )
                    file_fields[field_name] = saved_name
                continue

            if isinstance(field, models.ForeignKey):
                payload[field_name] = str(value.pk) if value else None
            elif value is None:
                payload[field_name] = None
            elif isinstance(value, Decimal):
                payload[field_name] = str(value)
            elif isinstance(value, (date, datetime)):
                payload[field_name] = value.isoformat()
            else:
                payload[field_name] = value

        return {
            'asset_name': cleaned_data.get('name', ''),
            'asset_category': cleaned_data.get('category').name if cleaned_data.get('category') else '',
            'asset_quantity': cleaned_data.get('quantity', 1),
            'asset_description': cleaned_data.get('description', ''),
            'asset_payload': payload,
            'file_fields': file_fields,
        }


class AssetImportView(LoginRequiredMixin, FormView):
    template_name = 'assets/asset_import.html'
    form_class = AssetImportForm
    success_url = reverse_lazy('asset-list')

    def post(self, request, *args, **kwargs):
        # Handle the confirm step (no file upload, data is in session)
        if 'confirm_create' in request.POST:
            return self._handle_confirm_import(request)
        return super().post(request, *args, **kwargs)

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
                raw_data = list(reader)
                # Normalize headers to lowercase with underscores
                for row in raw_data:
                    data.append(self._normalize_row_keys(row))
            except Exception as e:
                raise ValueError(f"Error reading CSV: {str(e)}")
        
        elif filename.endswith('.xlsx'):
            try:
                # Optimized Excel reading for large files
                wb = openpyxl.load_workbook(uploaded_file, data_only=True, read_only=True)
                sheet = wb.active
                
                # Get headers from the first row and normalize
                rows_gen = sheet.iter_rows(values_only=True)
                raw_headers = [h for h in next(rows_gen) if h]
                headers = [self._normalize_header(h) for h in raw_headers]
                
                for row in rows_gen:
                    if any(row):  # Skip empty rows
                        row_dict = dict(zip(headers, row))
                        data.append(row_dict)
                wb.close() # Important for read_only=True
            except Exception as e:
                raise ValueError(f"Error reading Excel: {str(e)}")
        
        return data

    # Header alias mapping: maps common variations to the expected field names
    HEADER_ALIASES = {
        'building name': 'building', 'bldg': 'building', 'bldg name': 'building',
        'floor name': 'floor', 'floor no': 'floor', 'floor number': 'floor',
        'room name': 'room', 'room no': 'room', 'room number': 'room',
        'branch name': 'branch', 'site name': 'site', 'region name': 'region',
        'location name': 'location', 'sub location': 'sub_location',
        'sub location name': 'sub_location', 'sublocation': 'sub_location',
        'sub category': 'sub_category', 'subcategory': 'sub_category',
        'sub group': 'sub_group', 'subgroup': 'sub_group',
        'department name': 'department', 'dept': 'department',
        'brand name': 'brand', 'company name': 'company',
        'supplier name': 'supplier', 'vendor name': 'vendor',
        'asset name': 'name', 'asset description': 'description',
        'erp asset number': 'erp_asset_number', 'erp number': 'erp_asset_number',
        'asset code': 'asset_code', 'asset type': 'asset_type',
        'label type': 'label_type', 'serial number': 'serial_number',
        'serial no': 'serial_number', 'cost center': 'cost_center',
        'employee number': 'employee_number', 'employee no': 'employee_number',
        'employee id': 'employee_number', 'emp no': 'employee_number',
        'purchase date': 'purchase_date', 'purchase price': 'purchase_price',
        'invoice number': 'invoice_number', 'invoice no': 'invoice_number',
        'invoice date': 'invoice_date', 'po number': 'po_number',
        'po date': 'po_date', 'do number': 'do_number', 'do date': 'do_date',
        'grn number': 'grn_number', 'grn no': 'grn_number',
        'warranty start': 'warranty_start', 'warranty end': 'warranty_end',
        'tagged date': 'tagged_date', 'short description': 'short_description',
        'date placed in service': 'date_placed_in_service',
        'insurance start date': 'insurance_start_date',
        'insurance end date': 'insurance_end_date',
        'maintenance start date': 'maintenance_start_date',
        'maintenance end date': 'maintenance_end_date',
        'next maintenance date': 'next_maintenance_date',
        'maintenance frequency days': 'maintenance_frequency_days',
        'maintenance frequency': 'maintenance_frequency_days',
        'expected units': 'expected_units',
        'useful life years': 'useful_life_years', 'useful life': 'useful_life_years',
        'salvage value': 'salvage_value', 'depreciation method': 'depreciation_method',
    }

    def _normalize_header(self, header):
        """Normalize a single header: lowercase, strip, replace spaces with underscores, apply aliases."""
        if not header:
            return ''
        h = str(header).strip().lower()
        # Check alias mapping first (before replacing spaces with underscores)
        if h in self.HEADER_ALIASES:
            return self.HEADER_ALIASES[h]
        # Replace spaces with underscores for standard field matching
        h = h.replace(' ', '_')
        if h in self.HEADER_ALIASES:
            return self.HEADER_ALIASES[h]
        return h

    def _normalize_row_keys(self, row):
        """Normalize all keys in a row dict."""
        return {self._normalize_header(k): v for k, v in row.items()}

    def parse_date(self, value):
        if not value:
            return None
        if isinstance(value, (datetime, date)):
            return value
        val_str = str(value).strip()
        if not val_str or val_str.lower() in ('none', 'null', 'nan'):
            return None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S',
                    '%d/%m/%Y %I:%M:%S %p', '%m/%d/%Y %I:%M:%S %p',
                    '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                    '%Y-%m-%d %I:%M:%S %p', '%d-%m-%Y', '%d-%m-%Y %H:%M:%S',
                    '%d-%m-%Y %I:%M:%S %p'):
            try:
                return datetime.strptime(val_str, fmt).date()
            except (ValueError, TypeError):
                continue
        return None

    def _build_cache(self, model, field='name', org=None):
        qs = model.objects.all()
        if org and hasattr(model, 'organization'):
            qs = qs.filter(organization=org)
        cache = {}
        for obj in qs:
            val = getattr(obj, field)
            if val:
                cache[str(val).strip().lower()] = obj
        return cache

    def _detect_new_entities(self, rows, org):
        """Scan rows and return sets of entity names that don't exist in the system."""
        categories_by_code = self._build_cache(Category, 'code', org)
        categories_by_name = self._build_cache(Category, 'name', org)
        subcategories = self._build_cache(SubCategory, 'name', org)
        groups = self._build_cache(Group, 'name', org)
        subgroups = self._build_cache(SubGroup, 'name', org)
        brands = self._build_cache(Brand, 'name', org)
        regions = self._build_cache(Region, 'name', org)
        sites = self._build_cache(Site, 'name', org)
        buildings = self._build_cache(Building, 'name', org)
        floors = self._build_cache(Floor, 'name', org)

        new_entities = {
            'categories': set(),
            'subcategories': set(),
            'groups': set(),
            'sub_groups': set(),
            'brands': set(),
            'regions': set(),
            'sites': set(),
            'buildings': set(),
            'floors': set(),
        }

        for row in rows:
            cat_val = str(row.get('category') or '').strip()
            if cat_val and not (categories_by_code.get(cat_val.lower()) or categories_by_name.get(cat_val.lower())):
                new_entities['categories'].add(cat_val)

            sub_val = str(row.get('sub_category') or '').strip()
            if sub_val and not subcategories.get(sub_val.lower()):
                new_entities['subcategories'].add(sub_val)

            grp_val = str(row.get('group') or '').strip()
            if grp_val and not groups.get(grp_val.lower()):
                new_entities['groups'].add(grp_val)

            sgrp_val = str(row.get('sub_group') or '').strip()
            if sgrp_val and not subgroups.get(sgrp_val.lower()):
                new_entities['sub_groups'].add(sgrp_val)

            brand_val = str(row.get('brand') or '').strip()
            if brand_val and not brands.get(brand_val.lower()):
                new_entities['brands'].add(brand_val)

            region_val = str(row.get('region') or '').strip()
            if region_val and not regions.get(region_val.lower()):
                new_entities['regions'].add(region_val)

            site_val = str(row.get('site') or '').strip()
            if site_val and not sites.get(site_val.lower()):
                new_entities['sites'].add(site_val)

            building_val = str(row.get('building') or '').strip()
            if building_val and not buildings.get(building_val.lower()):
                new_entities['buildings'].add(building_val)

            floor_val = str(row.get('floor') or '').strip()
            if floor_val and not floors.get(floor_val.lower()):
                new_entities['floors'].add(floor_val)

        # Filter out empty sets
        return {k: sorted(v) for k, v in new_entities.items() if v}

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

        # --- DETECT NEW ENTITIES ---
        new_entities = self._detect_new_entities(rows, org)

        if new_entities:
            # Store file data in session for the confirmation step
            serializable_rows = []
            for row in rows:
                serializable_row = {}
                for k, v in row.items():
                    if isinstance(v, (date, datetime)):
                        serializable_row[k] = v.isoformat()
                    elif v is None:
                        serializable_row[k] = ''
                    else:
                        serializable_row[k] = str(v)
                serializable_rows.append(serializable_row)

            self.request.session['import_rows'] = serializable_rows
            self.request.session['import_new_entities'] = new_entities

            return render(self.request, 'assets/asset_import_preview.html', {
                'new_entities': new_entities,
                'total_rows': len(rows),
            })

        # No new entities, proceed with import directly
        return self._process_import(rows, org)

    def _handle_confirm_import(self, request):
        """Handle the confirm step: auto-create entities, then import."""
        org = request.user.organization
        stored_rows = request.session.pop('import_rows', None)
        stored_entities = request.session.pop('import_new_entities', None)

        if not stored_rows:
            messages.error(request, "Import session expired. Please upload the file again.")
            return redirect('asset-import')

        rows = stored_rows
        new_entities = stored_entities or {}

        # Auto-create selected new entities
        selected = request.POST.getlist('create_entities')

        if 'categories' in selected:
            for name in new_entities.get('categories', []):
                Category.objects.get_or_create(organization=org, name=name)

        if 'subcategories' in selected:
            for name in new_entities.get('subcategories', []):
                parent_cat = None
                for row in rows:
                    if str(row.get('sub_category') or '').strip().lower() == name.lower():
                        cat_val = str(row.get('category') or '').strip()
                        if cat_val:
                            parent_cat = Category.objects.filter(
                                organization=org
                            ).filter(
                                models.Q(name__iexact=cat_val) | models.Q(code__iexact=cat_val)
                            ).first()
                        break
                if parent_cat:
                    SubCategory.objects.get_or_create(
                        organization=org, category=parent_cat, name=name
                    )

        if 'groups' in selected:
            for name in new_entities.get('groups', []):
                Group.objects.get_or_create(organization=org, name=name)

        if 'sub_groups' in selected:
            for name in new_entities.get('sub_groups', []):
                SubGroup.objects.get_or_create(organization=org, name=name)

        if 'brands' in selected:
            for name in new_entities.get('brands', []):
                Brand.objects.get_or_create(organization=org, name=name)

        if 'regions' in selected:
            for name in new_entities.get('regions', []):
                Region.objects.get_or_create(organization=org, name=name)

        if 'sites' in selected:
            for name in new_entities.get('sites', []):
                # Link site to its region from the file row
                parent_region = None
                for row in rows:
                    if str(row.get('site') or '').strip().lower() == name.lower():
                        region_val = str(row.get('region') or '').strip()
                        if region_val:
                            parent_region = Region.objects.filter(
                                organization=org, name__iexact=region_val
                            ).first()
                        break
                if parent_region:
                    Site.objects.get_or_create(
                        region=parent_region, name=name,
                        defaults={'organization': org}
                    )

        if 'buildings' in selected:
            for name in new_entities.get('buildings', []):
                # Link building to its branch from the file row
                parent_branch = None
                for row in rows:
                    if str(row.get('building') or '').strip().lower() == name.lower():
                        branch_val = str(row.get('branch') or '').strip()
                        if branch_val:
                            parent_branch = Branch.objects.filter(
                                organization=org, name__iexact=branch_val
                            ).first()
                        break
                if parent_branch:
                    Building.objects.get_or_create(
                        branch=parent_branch, name=name,
                        defaults={'organization': org}
                    )

        if 'floors' in selected:
            for name in new_entities.get('floors', []):
                # Link floor to its building from the file row
                parent_building = None
                for row in rows:
                    if str(row.get('floor') or '').strip().lower() == name.lower():
                        building_val = str(row.get('building') or '').strip()
                        if building_val:
                            parent_building = Building.objects.filter(
                                organization=org, name__iexact=building_val
                            ).first()
                        break
                if parent_building:
                    Floor.objects.get_or_create(
                        building=parent_building, name=name,
                        defaults={'organization': org}
                    )

        created_types = [t.replace('_', ' ').title() for t in selected]
        if created_types:
            messages.info(request, f"Auto-created: {', '.join(created_types)}")

        return self._process_import(rows, org)

    def _process_import(self, rows, org):
        def build_cache(model, field='name', org_relevant=True):
            qs = model.objects.all()
            if org_relevant and hasattr(model, 'organization'):
                qs = qs.filter(organization=org)
            elif org_relevant and hasattr(model, 'category') and hasattr(model.category, 'organization'):
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
        seen_asset_codes = set()

        # --- PROPER ASSET TAG GENERATION (CO-CAT-XXXX-YY) ---
        # Track counters per prefix so bulk rows auto-increment without DB round-trips
        from datetime import date as _date
        _year_suffix = str(_date.today().year)[-2:]
        _tag_counters = {}  # key: "CO-CAT", value: next hex counter (int)

        def _bulk_generate_tag(organization, category, company):
            """Generate tag with in-memory counter tracking, respecting org config."""
            sep = getattr(organization, 'tag_separator', '-') or '-'
            include_company = getattr(organization, 'tag_include_company', True)
            include_category = getattr(organization, 'tag_include_category', True)
            include_year = getattr(organization, 'tag_include_year', True)
            seq_fmt = getattr(organization, 'tag_sequence_format', 'HEX4') or 'HEX4'
            fixed_prefix = (getattr(organization, 'tag_prefix', '') or '').strip().upper()

            prefix_parts = []
            if fixed_prefix:
                prefix_parts.append(fixed_prefix)
            elif include_company:
                if company and company.name:
                    alpha = ''.join(c for c in company.name if c.isalpha()).upper()
                    co = alpha[:2] if len(alpha) >= 2 else alpha.ljust(2, 'X')[:2]
                else:
                    co = 'XX'
                prefix_parts.append(co)
            if include_category:
                cat_code = category.code[:3].upper() if category.code else 'XXX'
                prefix_parts.append(cat_code)

            prefix = sep.join(prefix_parts)
            total_parts = len(prefix_parts) + 1 + (1 if include_year else 0)
            seq_index = len(prefix_parts)

            if prefix not in _tag_counters:
                qs = Asset.objects.filter(
                    organization=organization,
                    asset_tag__startswith=prefix,
                )
                if include_year:
                    qs = qs.filter(asset_tag__endswith=f"{sep}{_year_suffix}")
                existing = qs.values_list('asset_tag', flat=True)
                max_num = 0
                for tag in existing:
                    try:
                        parts = tag.split(sep)
                        if len(parts) == total_parts:
                            cstr = parts[seq_index]
                            num = int(cstr, 16) if seq_fmt.startswith('HEX') else int(cstr)
                            if num > max_num:
                                max_num = num
                    except (ValueError, IndexError):
                        continue
                _tag_counters[prefix] = max_num + 1

            next_num = _tag_counters[prefix]
            _tag_counters[prefix] = next_num + 1

            fmt_map = {
                'HEX4': lambda n: f"{n:04X}", 'HEX6': lambda n: f"{n:06X}",
                'NUM4': lambda n: f"{n:04d}", 'NUM5': lambda n: f"{n:05d}", 'NUM6': lambda n: f"{n:06d}",
            }
            counter = fmt_map.get(seq_fmt, fmt_map['HEX4'])(next_num)
            all_parts = prefix_parts + [counter]
            if include_year:
                all_parts.append(_year_suffix)
            return sep.join(all_parts)

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

                company = get_from_cache(companies, row.get('company'))
                asset_tag = _bulk_generate_tag(org, category, company)

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
                    """Parse a numeric value robustly from CSV/Excel imports.

                    Accepts values like "5,000.00", "AED 5,000.00", "$5,000", "(5,000.00)" and returns Decimal or None.
                    """
                    if val is None:
                        return None
                    s = str(val).strip()
                    if s == '':
                        return None

                    # Handle parentheses for negative values: (1,234.56)
                    negative = False
                    if s.startswith('(') and s.endswith(')'):
                        negative = True
                        s = s[1:-1].strip()

                    # Remove any currency letters/symbols but keep digits, dot, comma and minus
                    try:
                        import re
                        s = re.sub(r"[^0-9.,\-]", "", s)
                    except Exception:
                        # Fallback: remove common non-numeric chars
                        s = s.replace('AED', '').replace('$', '').replace('USD', '')

                    # Normalize commas and dots (remove thousands separators)
                    s = s.replace(',', '')

                    if s in ('', '-', '.'):
                        return None

                    try:
                        d = Decimal(s)
                        return -d if negative else d
                    except Exception:
                        return None
                
                def parse_int(val, default=None):
                    if val is None or str(val).strip() == '': return default
                    try: return int(float(str(val)))
                    except: return default

                # Validate asset_code (required + unique)
                asset_code_val = str(row.get('asset_code') or '').strip()
                if not asset_code_val:
                    errors.append(f"Row {row_idx}: asset_code is required.")
                    continue
                if asset_code_val in seen_asset_codes:
                    errors.append(f"Row {row_idx}: Duplicate asset_code '{asset_code_val}' in file.")
                    continue
                seen_asset_codes.add(asset_code_val)
                if Asset.objects.filter(organization=org, asset_code=asset_code_val).exists():
                    errors.append(f"Row {row_idx}: asset_code '{asset_code_val}' already exists.")
                    continue

                # Create Asset Instance (in memory)
                asset = Asset(
                    organization=org,
                    created_by=self.request.user,
                    name=name,
                    description=str(row.get('description') or ''),
                    short_description=str(row.get('short_description') or ''),
                    asset_tag=asset_tag,
                    asset_code=asset_code_val,
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
            return redirect('asset-import')

        # --- BULK SAVE ---
        try:
            with transaction.atomic():
                # Process in batches of 1000 for stability
                Asset.objects.bulk_create(assets_to_create, batch_size=1000)

            # Generate QR codes and barcodes for all imported assets
            from .code_generators import generate_codes_for_asset
            generated_count = 0
            for asset in assets_to_create:
                try:
                    # Refresh from DB to get the pk assigned by bulk_create
                    db_asset = Asset.objects.get(
                        organization=org, asset_tag=asset.asset_tag
                    )
                    generate_codes_for_asset(db_asset)
                    generated_count += 1
                except Exception:
                    pass  # Non-critical: asset created but code generation failed

            messages.success(
                self.request,
                f"Successfully imported {len(assets_to_create)} assets. "
                f"QR/Barcode generated for {generated_count} assets."
            )
        except Exception as e:
            messages.error(self.request, f"Database error during bulk save: {str(e)}")
            return redirect('asset-import')

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
            form.instance.asset_tag = generate_asset_tag(
                self.request.user.organization,
                form.instance.category,
                form.instance.company
            )
        return super().form_valid(form)

# --- CATEGORY VIEWS ---
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'assets/configuration/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(
            organization=self.request.user.organization
        ).annotate(asset_count=Count('asset'))

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
from apps.users.views import ApprovalAccessMixin, CheckerRequiredMixin, SeniorManagerRequiredMixin, EmployeeRequiredMixin

class ApprovalListView(ApprovalAccessMixin, TemplateView):
    """Unified approvals dashboard showing both asset approvals and disposal requests"""
    template_name = 'assets/approval_list.html'
    
    def get_disposal_queryset(self):
        """Get relevant disposal approvals based on user role"""
        user = self.request.user
        org = user.organization
        
        # Managers see PENDING disposals to review
        if user.role in [user.Role.SENIOR_MANAGER, user.Role.CHECKER]:
            return AssetDisposal.objects.filter(
                organization=org,
                status=AssetDisposal.Status.PENDING
            ).order_by('-created_at')
        
        # Admins see MANAGER_APPROVED disposals awaiting final approval
        elif user.is_superuser or user.role == user.Role.ADMIN:
            return AssetDisposal.objects.filter(
                organization=org,
                status=AssetDisposal.Status.MANAGER_APPROVED
            ).order_by('-created_at')
        
        # Employees see their own disposal requests
        elif user.role == user.Role.EMPLOYEE:
            return AssetDisposal.objects.filter(
                organization=org,
                requested_by=user
            ).order_by('-created_at')
        
        return AssetDisposal.objects.none()
    
    def get_asset_approval_queryset(self):
        """Get relevant asset approval requests based on user role"""
        user = self.request.user
        
        # Checkers see pending requests
        if user.is_checker:
            return ApprovalRequest.objects.filter(
                organization=user.organization,
                status=ApprovalRequest.Status.PENDING
            ).order_by('-created_at')
        
        # Senior managers see checker-approved requests
        elif user.is_senior_manager:
            return ApprovalRequest.objects.filter(
                organization=user.organization,
                status=ApprovalRequest.Status.CHECKER_APPROVED
            ).order_by('-created_at')
        
        # Employees can see only their own
        elif user.role == user.Role.EMPLOYEE:
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
        
        # Get disposals
        disposals = self.get_disposal_queryset()
        
        # Get asset approvals
        asset_approvals = self.get_asset_approval_queryset()
        
        # Combine all for unified list (sort by created_at)
        all_approvals = []
        for disposal in disposals:
            all_approvals.append({
                'type': 'disposal',
                'id': disposal.id,
                'pk': disposal.pk,
                'asset': disposal.asset,
                'status': disposal.status,
                'get_status_display': disposal.get_status_display(),
                'created_at': disposal.created_at,
                'requested_by': disposal.requested_by,
                'get_disposal_method_display': disposal.get_disposal_method_display(),
                'disposal_method': disposal.disposal_method,
                'manager_approved_by': disposal.manager_approved_by,
                'can_approve': (user.role in [user.Role.SENIOR_MANAGER, user.Role.CHECKER] and disposal.status == AssetDisposal.Status.PENDING) or 
                               (user.is_superuser or user.role == user.Role.ADMIN) and disposal.status == AssetDisposal.Status.MANAGER_APPROVED
            })
        
        for approval in asset_approvals:
            all_approvals.append({
                'type': 'asset',
                'id': approval.id,
                'pk': approval.pk,
                'asset': approval.asset,
                'asset_name': approval.asset.name if approval.asset else 'N/A',
                'status': approval.status,
                'get_status_display': approval.get_status_display(),
                'created_at': approval.created_at,
                'requester': approval.requester,
                'request_type': approval.get_request_type_display(),
                'can_approve': approval.status in [ApprovalRequest.Status.PENDING, ApprovalRequest.Status.CHECKER_APPROVED]
            })
        
        # Sort by created_at
        all_approvals.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Calculate stats
        disposal_pending = AssetDisposal.objects.filter(
            organization=user.organization,
            status=AssetDisposal.Status.PENDING
        ).count()
        
        asset_pending = ApprovalRequest.objects.filter(
            organization=user.organization,
            status=ApprovalRequest.Status.PENDING
        ).count()
        
        # Add to context
        context['disposals'] = disposals
        context['asset_approvals'] = asset_approvals
        context['all_approvals'] = all_approvals
        context['disposal_pending'] = disposals.filter(status=AssetDisposal.Status.PENDING).count()
        context['asset_pending'] = asset_approvals.filter(status=ApprovalRequest.Status.PENDING).count()
        context['total_pending'] = context['disposal_pending'] + context['asset_pending']
        context['total_approved'] = disposals.filter(status=AssetDisposal.Status.APPROVED).count() + \
                                   asset_approvals.filter(status=ApprovalRequest.Status.APPROVED).count()
        context['total_rejected'] = disposals.filter(status=AssetDisposal.Status.REJECTED).count() + \
                                   asset_approvals.filter(status=ApprovalRequest.Status.PENDING).count()
        
        return context


class ApprovalDetailView(ApprovalAccessMixin, DetailView):
    """View approval request details"""
    model = ApprovalRequest
    template_name = 'assets/approval_detail.html'
    context_object_name = 'approval'
    
    def get_queryset(self):
        user = self.request.user
        qs = ApprovalRequest.objects.filter(organization=user.organization)
        # Admins and approvers may view all requests
        if user.is_superuser or user.role == user.Role.ADMIN or user.is_checker or user.is_senior_manager:
            return qs
        # Employees may view only their own requests
        if user.role == user.Role.EMPLOYEE:
            return qs.filter(requester=user)
        return ApprovalRequest.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approval = self.object
        context['approval_logs'] = approval.approval_logs.all().order_by('-created_at')
        # Only admins (or superusers) can perform approval actions
        is_admin = self.request.user.is_superuser or self.request.user.role == self.request.user.Role.ADMIN
        context['can_approve_checker'] = is_admin and approval.needs_checker_approval
        context['can_approve_senior'] = is_admin and approval.needs_senior_approval
        return context


class ApprovalApproveView(LoginRequiredMixin, View):
    """Approve an approval request"""
    
    def post(self, request, pk):
        approval = get_object_or_404(ApprovalRequest, pk=pk, organization=request.user.organization)
        user = request.user
        
        decision = request.POST.get('decision')  # 'APPROVED' or 'REJECTED'
        comments = request.POST.get('comments', '')
        
        # Only admins (or superusers) can approve; they advance the request through the workflow
        if (user.is_superuser or user.role == user.Role.ADMIN) and approval.status == ApprovalRequest.Status.PENDING:
            if decision == 'APPROVED':
                approval.status = ApprovalRequest.Status.CHECKER_APPROVED
                messages.success(request, 'Request approved. Pending senior manager approval.')
            elif decision == 'REJECTED':
                approval.status = ApprovalRequest.Status.CHECKER_REJECTED
                messages.warning(request, 'Request rejected.')
            approval.save()
            ApprovalLog.objects.create(
                approval_request=approval,
                approver=user,
                decision=decision,
                approval_level='CHECKER',
                comments=comments,
                organization=user.organization
            )
        elif (user.is_superuser or user.role == user.Role.ADMIN) and approval.status == ApprovalRequest.Status.CHECKER_APPROVED:
            if decision == 'APPROVED':
                approval.status = ApprovalRequest.Status.APPROVED
                messages.success(request, 'Request fully approved!')
            elif decision == 'REJECTED':
                approval.status = ApprovalRequest.Status.SENIOR_REJECTED
                messages.warning(request, 'Request rejected.')
            approval.save()
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


class CreateApprovalRequestView(EmployeeRequiredMixin, CreateView):
    """Employee creates approval request for new asset"""
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
        user = request.user
        # Define available reports
        reports = []
        
        # Only show Depreciation Reports to non-EMPLOYEE users (or superusers)
        if user.role != user.Role.EMPLOYEE or user.is_superuser:
            reports.append({
                'name': 'Depreciation Report',
                'description': 'Full asset-level depreciation schedule showing cost, accumulated depreciation, net book value and remaining life for every asset.',
                'icon': 'file-text',
                'url': reverse('depreciation-report'),
                'color': 'warning'
            })
            reports.append({
                'name': 'Depreciation by Category',
                'description': 'View asset depreciation grouped by category with book value, accumulated depreciation, and remaining life.',
                'icon': 'trending-down',
                'url': reverse('depreciation-category'),
                'color': 'info'
            })
            reports.append({
                'name': 'Depreciation by Group',
                'description': 'Analyze depreciation across asset groups for consolidated financial reporting.',
                'icon': 'bar-chart-2',
                'url': reverse('depreciation-group'),
                'color': 'info'
            })
            reports.append({
                'name': 'Depreciation by Location',
                'description': 'Location-wise depreciation summary to track asset value across branches and sites.',
                'icon': 'map-pin',
                'url': reverse('depreciation-location'),
                'color': 'info'
            })
            reports.append({
                'name': 'Depreciation by Department',
                'description': 'Department-wise depreciation breakdown for cost allocation and budgeting.',
                'icon': 'building-2',
                'url': reverse('depreciation-department'),
                'color': 'info'
            })
        
        # Asset Inventory - visible to all
        reports.append({
            'name': 'Asset Inventory',
            'description': 'Complete list of all assets with filters, search, and export to Excel.',
            'icon': 'package',
            'url': reverse('asset-list'),
            'color': 'primary'
        })

        # Masters Report - full asset register with all fields
        reports.append({
            'name': 'Asset Register (Masters)',
            'description': 'Comprehensive asset register with all details — export full data to Excel.',
            'icon': 'table',
            'url': reverse('masters-list'),
            'color': 'primary'
        })

        # Transfer Report
        reports.append({
            'name': 'Transfer Report',
            'description': 'View all asset transfers with status, dates, and export to Excel.',
            'icon': 'arrow-right-left',
            'url': reverse('transfer-list'),
            'color': 'warning'
        })

        # Disposal Report
        reports.append({
            'name': 'Disposal Report',
            'description': 'Track disposed assets with approval status, disposal method, and value recovered.',
            'icon': 'trash-2',
            'url': reverse('disposal-list'),
            'color': 'danger'
        })

        # Asset Export
        reports.append({
            'name': 'Export Assets (Excel)',
            'description': 'Download a full Excel export of all assets with current filters applied.',
            'icon': 'download',
            'url': reverse('asset-export-excel'),
            'color': 'success'
        })

        # Asset Approvals - only for users with approval permissions
        if user.can_approve:
            reports.append({
                'name': 'Asset Approvals',
                'description': 'View and manage pending and completed asset approval requests.',
                'icon': 'check-circle',
                'url': reverse('approval_list'),
                'color': 'success'
            })
        
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
            'is_paginated': page_obj.has_other_pages(),
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


class MastersExportExcelView(LoginRequiredMixin, View):
    """Export masters data to Excel with all fields and applied filters"""
    
    def get(self, request):
        from django.core.paginator import Paginator
        from django.db.models import Q
        organization = request.user.organization
        
        # Get same filters as MastersListView
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
        
        # Build queryset with same logic as MastersListView
        assets_qs = Asset.objects.filter(
            organization=organization
        ).select_related(
            'category', 'sub_category', 'group', 'sub_group', 'brand_new',
            'company', 'supplier', 'custodian', 'department', 'assigned_to',
            'branch', 'building', 'floor', 'room', 'region', 'site', 
            'location', 'sub_location', 'vendor', 'asset_remarks', 'parent'
        )
        
        # Apply filters
        if search_query:
            assets_qs = assets_qs.filter(
                Q(asset_tag__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(serial_number__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        if category_filter:
            assets_qs = assets_qs.filter(category_id=category_filter)
        if sub_category_filter:
            assets_qs = assets_qs.filter(sub_category_id=sub_category_filter)
        if company_filter:
            assets_qs = assets_qs.filter(company_id=company_filter)
        if department_filter:
            assets_qs = assets_qs.filter(department_id=department_filter)
        if condition_filter:
            assets_qs = assets_qs.filter(condition=condition_filter)
        if status_filter:
            assets_qs = assets_qs.filter(status=status_filter)
        if brand_filter:
            assets_qs = assets_qs.filter(brand_new_id=brand_filter)
        if vendor_filter:
            assets_qs = assets_qs.filter(vendor_id=vendor_filter)
        if supplier_filter:
            assets_qs = assets_qs.filter(supplier_id=supplier_filter)
        if group_filter:
            assets_qs = assets_qs.filter(group_id=group_filter)
        if subgroup_filter:
            assets_qs = assets_qs.filter(sub_group_id=subgroup_filter)
        if custodian_filter:
            assets_qs = assets_qs.filter(custodian_id=custodian_filter)
        if purchase_date_from:
            try:
                from_date = datetime.strptime(purchase_date_from, '%Y-%m-%d').date()
                assets_qs = assets_qs.filter(purchase_date__gte=from_date)
            except:
                pass
        if purchase_date_to:
            try:
                to_date = datetime.strptime(purchase_date_to, '%Y-%m-%d').date()
                assets_qs = assets_qs.filter(purchase_date__lte=to_date)
            except:
                pass
        
        # Apply sorting
        if sort_by:
            assets_qs = assets_qs.order_by(sort_by)
        
        # Create Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asset Masters"
        
        # Add export information at the top
        current_row = 1
        ws.merge_cells(f'A{current_row}:E{current_row}')
        cell = ws.cell(row=current_row, column=1)
        cell.value = "ASSET MASTER DATA EXPORT"
        cell.font = openpyxl.styles.Font(size=14, bold=True)
        cell.alignment = openpyxl.styles.Alignment(horizontal='left')
        current_row += 1
        
        ws.cell(row=current_row, column=1, value="Export Date:")
        ws.cell(row=current_row, column=2, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ws.cell(row=current_row, column=1).font = openpyxl.styles.Font(bold=True)
        current_row += 1
        
        ws.cell(row=current_row, column=1, value="Total Records:")
        ws.cell(row=current_row, column=2, value=assets_qs.count())
        ws.cell(row=current_row, column=1).font = openpyxl.styles.Font(bold=True)
        current_row += 1
        
        # Add filter information if any filters are applied
        filters_applied = []
        if search_query:
            filters_applied.append(f"Search: {search_query}")
        if category_filter:
            try:
                cat = Category.objects.get(id=category_filter)
                filters_applied.append(f"Category: {cat.name}")
            except:
                pass
        if sub_category_filter:
            try:
                subcat = SubCategory.objects.get(id=sub_category_filter)
                filters_applied.append(f"Sub Category: {subcat.name}")
            except:
                pass
        if company_filter:
            try:
                comp = Company.objects.get(id=company_filter)
                filters_applied.append(f"Company: {comp.name}")
            except:
                pass
        if department_filter:
            try:
                dept = Department.objects.get(id=department_filter)
                filters_applied.append(f"Department: {dept.name}")
            except:
                pass
        if brand_filter:
            try:
                brand = Brand.objects.get(id=brand_filter)
                filters_applied.append(f"Brand: {brand.name}")
            except:
                pass
        if vendor_filter:
            try:
                vendor = Vendor.objects.get(id=vendor_filter)
                filters_applied.append(f"Vendor: {vendor.name}")
            except:
                pass
        if supplier_filter:
            try:
                supplier = Supplier.objects.get(id=supplier_filter)
                filters_applied.append(f"Supplier: {supplier.name}")
            except:
                pass
        if group_filter:
            try:
                group = Group.objects.get(id=group_filter)
                filters_applied.append(f"Group: {group.name}")
            except:
                pass
        if subgroup_filter:
            try:
                subgrp = SubGroup.objects.get(id=subgroup_filter)
                filters_applied.append(f"Sub Group: {subgrp.name}")
            except:
                pass
        if custodian_filter:
            try:
                custodian = Custodian.objects.get(id=custodian_filter)
                cust_name = custodian.user.get_full_name() if custodian.user else custodian.employee_id
                filters_applied.append(f"Custodian: {cust_name}")
            except:
                pass
        if condition_filter:
            cond_display = dict(Asset._meta.get_field('condition').choices).get(condition_filter, condition_filter)
            filters_applied.append(f"Condition: {cond_display}")
        if status_filter:
            status_display = dict(Asset._meta.get_field('status').choices).get(status_filter, status_filter)
            filters_applied.append(f"Status: {status_display}")
        if purchase_date_from:
            filters_applied.append(f"Purchase Date From: {purchase_date_from}")
        if purchase_date_to:
            filters_applied.append(f"Purchase Date To: {purchase_date_to}")
        
        if filters_applied:
            current_row += 1
            ws.cell(row=current_row, column=1, value="Applied Filters:")
            ws.cell(row=current_row, column=1).font = openpyxl.styles.Font(bold=True)
            current_row += 1
            for filter_text in filters_applied:
                ws.cell(row=current_row, column=1, value=f"  • {filter_text}")
                current_row += 1
        else:
            current_row += 1
            ws.cell(row=current_row, column=1, value="Filters: None (All assets)")
            ws.cell(row=current_row, column=1).font = openpyxl.styles.Font(italic=True)
            current_row += 1
        
        current_row += 1  # Empty row before data
        
        # Define headers (matching the table columns)
        headers = [
            'Asset Tag', 'Name', 'Category', 'Sub Category', 'Asset Type', 'Group', 'Sub Group',
            'Brand', 'Model', 'Condition', 'Serial Number', 'Supplier', 'Vendor', 'Company',
            'Department', 'Custodian', 'Employee Number', 'Region', 'Branch', 'Building', 
            'Floor', 'Room', 'Location', 'Site', 'Purchase Date', 'Purchase Price', 'Currency',
            'Invoice Number', 'PO Number', 'GRN Number', 'Warranty Start', 'Warranty End',
            'Tagged Date', 'Maintenance Start', 'Maintenance Frequency (Days)', 'Next Maintenance',
            'Useful Life (Years)', 'Salvage Value', 'Depreciation Method', 'Status', 'Remarks'
        ]
        
        # Add headers at current_row
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col_num, value=header)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = openpyxl.styles.Alignment(horizontal='center', vertical='center')
        
        current_row += 1
        
        # Add data rows
        for asset in assets_qs:
            row = [
                asset.asset_tag or '',
                asset.name or '',
                asset.category.name if asset.category else '',
                asset.sub_category.name if asset.sub_category else '',
                asset.asset_type or '',
                asset.group.name if asset.group else '',
                asset.sub_group.name if asset.sub_group else '',
                asset.brand_new.name if asset.brand_new else '',
                asset.model or '',
                asset.get_condition_display() if asset.condition else '',
                asset.serial_number or '',
                asset.supplier.name if asset.supplier else '',
                asset.vendor.name if asset.vendor else '',
                asset.company.name if asset.company else '',
                asset.department.name if asset.department else '',
                asset.custodian.user.get_full_name() if asset.custodian and asset.custodian.user else (asset.custodian.employee_id if asset.custodian else ''),
                asset.employee_number or '',
                asset.region.name if asset.region else '',
                asset.branch.name if asset.branch else '',
                asset.building.name if asset.building else '',
                asset.floor.name if asset.floor else '',
                asset.room.name if asset.room else '',
                asset.location.name if asset.location else '',
                asset.site.name if asset.site else '',
                asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else '',
                float(asset.purchase_price) if asset.purchase_price else '',
                asset.currency or '',
                asset.invoice_number or '',
                asset.po_number or '',
                asset.grn_number or '',
                asset.warranty_start.strftime('%Y-%m-%d') if asset.warranty_start else '',
                asset.warranty_end.strftime('%Y-%m-%d') if asset.warranty_end else '',
                asset.tagged_date.strftime('%Y-%m-%d') if asset.tagged_date else '',
                asset.maintenance_start_date.strftime('%Y-%m-%d') if asset.maintenance_start_date else '',
                asset.maintenance_frequency_days or '',
                asset.next_maintenance_date.strftime('%Y-%m-%d') if asset.next_maintenance_date else '',
                asset.useful_life_years or '',
                float(asset.salvage_value) if asset.salvage_value else '',
                asset.get_depreciation_method_display() if asset.depreciation_method else '',
                asset.get_status_display() if asset.status else '',
                asset.notes or (asset.asset_remarks.name if asset.asset_remarks else ''),
            ]
            
            # Add row at current position
            for col_num, value in enumerate(row, 1):
                ws.cell(row=current_row, column=col_num, value=value)
            current_row += 1
        
        # Auto-adjust column widths
        # Use explicit row/column indexing to avoid MergedCell issues from merged title cells.
        for col_idx in range(1, ws.max_column + 1):
            max_length = 0
            column_letter = openpyxl.utils.get_column_letter(col_idx)

            for row_idx in range(1, ws.max_row + 1):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if cell_value is None:
                    continue
                cell_length = len(str(cell_value))
                if cell_length > max_length:
                    max_length = cell_length

            adjusted_width = min(max_length + 2, 50) if max_length > 0 else 12
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Prepare response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="asset_masters_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response


# ========================
# Asset Transfer Views
# ========================

class AssetTransferListView(LoginRequiredMixin, ListView):
    """List all asset transfers with filtering"""
    model = AssetTransfer
    template_name = 'assets/transfer_list.html'
    context_object_name = 'transfers'
    paginate_by = 50

    def get_filtered_queryset(self):
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

        # Employees can create transfers but should only view transfers they initiated or are involved in
        user = self.request.user
        if user.role == user.Role.EMPLOYEE:
            queryset = queryset.filter(
                Q(created_by=user) | Q(transferred_to_user=user) | Q(transferred_from_user=user)
            )

        return queryset.order_by('-transfer_date')
    
    def get_queryset(self):
        return self.get_filtered_queryset()
    
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


class AssetTransferExportExcelView(AssetTransferListView):
    """Export filtered asset transfers to Excel."""

    def get(self, request, *args, **kwargs):
        transfers = self.get_filtered_queryset()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asset Transfers"

        headers = [
            'Transfer No', 'Asset Tag', 'Asset Name', 'From', 'To',
            'Transfer Reason', 'Status', 'Transfer Date', 'Created By'
        ]
        ws.append(headers)

        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        for transfer in transfers:
            from_value = '-'
            if transfer.transferred_from_user:
                from_value = transfer.transferred_from_user.get_full_name() or transfer.transferred_from_user.username
            elif transfer.transferred_from_department:
                from_value = transfer.transferred_from_department.name

            to_value = '-'
            if transfer.transferred_to_user:
                to_value = transfer.transferred_to_user.get_full_name() or transfer.transferred_to_user.username
            elif transfer.transferred_to_department:
                to_value = transfer.transferred_to_department.name

            created_by_value = '-'
            if transfer.created_by:
                created_by_value = transfer.created_by.get_full_name() or transfer.created_by.username

            ws.append([
                transfer.transfer_no or '',
                transfer.asset.asset_tag if transfer.asset else '',
                transfer.asset.name if transfer.asset else '',
                from_value,
                to_value,
                transfer.transfer_reason or '',
                transfer.get_status_display(),
                transfer.transfer_date.strftime('%Y-%m-%d %H:%M:%S') if transfer.transfer_date else '',
                created_by_value,
            ])

        for col_idx in range(1, ws.max_column + 1):
            max_length = 0
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            for row_idx in range(1, ws.max_row + 1):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if cell_value is None:
                    continue
                max_length = max(max_length, len(str(cell_value)))
            ws.column_dimensions[col_letter].width = min(max_length + 2, 45) if max_length else 12

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="asset_transfers_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response


class AssetTransferCreateView(LoginRequiredMixin, CreateView):
    """Create a new asset transfer"""
    model = AssetTransfer
    form_class = AssetTransferForm
    template_name = 'assets/transfer_form.html'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.role == user.Role.EMPLOYEE or user.is_superuser):
            messages.error(request, 'Only employees can create asset transfer requests.')
            return redirect('transfer-list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        # Support multiple assets: frontend may submit comma-separated asset IDs in `asset` field
        asset_field = form.cleaned_data.get('asset') or self.request.POST.get('asset', '')
        # Normalize to list of ids (strings)
        if asset_field and isinstance(asset_field, str) and ',' in asset_field:
            asset_ids = [s.strip() for s in asset_field.split(',') if s.strip()]
        elif hasattr(asset_field, 'pk'):
            asset_ids = [str(asset_field.pk)]
        elif asset_field:
            asset_ids = [str(asset_field)]
        else:
            asset_ids = []

        created = []
        if asset_ids:
            for aid in asset_ids:
                try:
                    asset_obj = Asset.objects.get(pk=aid, organization=self.request.user.organization)
                except Asset.DoesNotExist:
                    continue

                at = AssetTransfer.objects.create(
                    organization=self.request.user.organization,
                    created_by=self.request.user,
                    asset=asset_obj,
                    transfer_no=form.cleaned_data.get('transfer_no'),
                    transfer_description=form.cleaned_data.get('transfer_description'),
                    transferred_to_region=form.cleaned_data.get('transferred_to_region'),
                    transferred_to_site=form.cleaned_data.get('transferred_to_site'),
                    transferred_to_building=form.cleaned_data.get('transferred_to_building'),
                    transferred_to_floor=form.cleaned_data.get('transferred_to_floor'),
                    transferred_to_room=form.cleaned_data.get('transferred_to_room'),
                    transferred_to_company=form.cleaned_data.get('transferred_to_company'),
                    transferred_to_department=form.cleaned_data.get('transferred_to_department'),
                    transferred_to_custodian=form.cleaned_data.get('transferred_to_custodian'),
                    movement_reason=form.cleaned_data.get('movement_reason'),
                    requester_name=form.cleaned_data.get('requester_name'),
                )
                created.append(at)

            if created:
                # Redirect to the first created transfer
                messages.success(self.request, f'Asset transfer created for {len(created)} asset(s)')
                return redirect(reverse('transfer-detail', kwargs={'pk': created[0].pk}))
            else:
                form.add_error(None, 'No valid assets were provided')
                return self.form_invalid(form)

        # Fallback: single asset (normal flow)
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
        qs = AssetTransfer.objects.filter(organization=org).select_related(
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
        # Employees may view only transfers they created or where they're involved
        user = self.request.user
        if user.role == user.Role.EMPLOYEE:
            qs = qs.filter(Q(created_by=user) | Q(transferred_to_user=user) | Q(transferred_from_user=user))
        return qs


class AssetTransferUpdateView(LoginRequiredMixin, UpdateView):
    """Update an asset transfer (mainly for status changes)"""
    model = AssetTransfer
    form_class = AssetTransferForm
    template_name = 'assets/transfer_form.html'

    def _is_transfer_approver(self):
        user = self.request.user
        return user.is_superuser or user.role in [user.Role.ADMIN, user.Role.SENIOR_MANAGER]

    def dispatch(self, request, *args, **kwargs):
        if not self._is_transfer_approver():
            return HttpResponseForbidden('Only senior manager or admin can approve or update asset transfers.')
        return super().dispatch(request, *args, **kwargs)
    
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

    def _is_transfer_approver(self):
        user = self.request.user
        return user.is_superuser or user.role in [user.Role.ADMIN, user.Role.SENIOR_MANAGER]

    def dispatch(self, request, *args, **kwargs):
        if not self._is_transfer_approver():
            return HttpResponseForbidden('Only senior manager or admin can approve asset transfer requests.')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        org = self.request.user.organization
        return AssetTransfer.objects.filter(organization=org)
    
    def form_valid(self, form):
        form.instance.received_by = self.request.user
        user = self.request.user
        is_final_approver = user.is_superuser or user.role in [user.Role.ADMIN, user.Role.SENIOR_MANAGER]

        if form.instance.status == AssetTransfer.Status.RECEIVED:
            if not form.instance.actual_receipt_date:
                form.instance.actual_receipt_date = date.today()

            if is_final_approver and form.instance.asset:
                asset = form.instance.asset
                transfer = form.instance
                fields_to_update = []

                if transfer.transferred_to_user is not None:
                    asset.assigned_to = transfer.transferred_to_user
                    fields_to_update.append('assigned_to')
                if transfer.transferred_to_department is not None:
                    asset.department = transfer.transferred_to_department
                    fields_to_update.append('department')
                    if getattr(transfer.transferred_to_department, 'branch', None) is not None:
                        asset.branch = transfer.transferred_to_department.branch
                        fields_to_update.append('branch')
                if transfer.transferred_to_location is not None:
                    asset.location = transfer.transferred_to_location
                    fields_to_update.append('location')
                if transfer.transferred_to_region is not None:
                    asset.region = transfer.transferred_to_region
                    fields_to_update.append('region')
                if transfer.transferred_to_site is not None:
                    asset.site = transfer.transferred_to_site
                    fields_to_update.append('site')
                if transfer.transferred_to_building is not None:
                    asset.building = transfer.transferred_to_building
                    fields_to_update.append('building')
                    if getattr(transfer.transferred_to_building, 'branch', None) is not None:
                        asset.branch = transfer.transferred_to_building.branch
                        fields_to_update.append('branch')
                if transfer.transferred_to_floor is not None:
                    asset.floor = transfer.transferred_to_floor
                    fields_to_update.append('floor')
                if transfer.transferred_to_room is not None:
                    asset.room = transfer.transferred_to_room
                    fields_to_update.append('room')
                if transfer.transferred_to_company is not None:
                    asset.company = transfer.transferred_to_company
                    fields_to_update.append('company')
                if transfer.transferred_to_custodian is not None:
                    asset.custodian = transfer.transferred_to_custodian
                    fields_to_update.append('custodian')

                if fields_to_update:
                    asset.save(update_fields=list(dict.fromkeys(fields_to_update)))

            messages.success(self.request, f'Asset transfer marked as received: {form.instance.asset.asset_tag}')
        elif form.instance.status == AssetTransfer.Status.REJECTED:
            messages.warning(self.request, f'Asset transfer rejected: {form.instance.asset.asset_tag}')
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('transfer-detail', kwargs={'pk': self.object.pk})


# ========================
# Asset Disposal Views
# ========================

class AssetDisposalListView(LoginRequiredMixin, ListView):
    """List asset disposal requests"""
    model = AssetDisposal
    template_name = 'assets/disposal_list.html'
    context_object_name = 'disposals'
    paginate_by = 50
    
    def get_queryset(self):
        org = self.request.user.organization
        qs = AssetDisposal.objects.filter(organization=org).select_related(
            'asset', 'requested_by', 'approved_by'
        )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        # Search by asset tag or name
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(asset__asset_tag__icontains=search) |
                Q(asset__name__icontains=search)
            )
        
        # Employees can see only their own disposal requests
        user = self.request.user
        if user.role == user.Role.EMPLOYEE:
            qs = qs.filter(requested_by=user)
        
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = AssetDisposal.Status.choices
        context['status_filter'] = self.request.GET.get('status', '')
        context['search'] = self.request.GET.get('search', '')
        return context


class AssetDisposalExportExcelView(AssetDisposalListView):
    """Export filtered asset disposals to Excel."""

    def get(self, request, *args, **kwargs):
        disposals = self.get_queryset()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asset Disposals"

        headers = [
            'Asset Tag', 'Asset Name', 'Requested By', 'Disposal Method',
            'Reason', 'Status', 'Disposal Date', 'Estimated Salvage Value',
            'Manager Approved By', 'Manager Approved At',
            'Admin Approved By', 'Admin Approved At', 'Notes', 'Created Date'
        ]
        ws.append(headers)

        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        for disposal in disposals:
            requested_by = '-'
            if disposal.requested_by:
                requested_by = disposal.requested_by.get_full_name() or disposal.requested_by.username

            manager_approved_by = '-'
            if disposal.manager_approved_by:
                manager_approved_by = disposal.manager_approved_by.get_full_name() or disposal.manager_approved_by.username

            admin_approved_by = '-'
            if disposal.approved_by:
                admin_approved_by = disposal.approved_by.get_full_name() or disposal.approved_by.username

            ws.append([
                disposal.asset.asset_tag if disposal.asset else '',
                disposal.asset.name if disposal.asset else '',
                requested_by,
                disposal.get_disposal_method_display(),
                disposal.reason or '',
                disposal.get_status_display(),
                disposal.disposal_date.strftime('%Y-%m-%d') if disposal.disposal_date else '',
                str(disposal.estimated_salvage_value) if disposal.estimated_salvage_value else '',
                manager_approved_by,
                disposal.manager_approved_at.strftime('%Y-%m-%d %H:%M:%S') if disposal.manager_approved_at else '',
                admin_approved_by,
                disposal.approved_at.strftime('%Y-%m-%d %H:%M:%S') if disposal.approved_at else '',
                disposal.notes or '',
                disposal.created_at.strftime('%Y-%m-%d %H:%M:%S') if disposal.created_at else '',
            ])

        for col_idx in range(1, ws.max_column + 1):
            max_length = 0
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            for row_idx in range(1, ws.max_row + 1):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if cell_value is None:
                    continue
                max_length = max(max_length, len(str(cell_value)))
            ws.column_dimensions[col_letter].width = min(max_length + 2, 45) if max_length else 12

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="asset_disposals_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        wb.save(response)
        return response


class AssetDisposalCreateView(EmployeeRequiredMixin, CreateView):
    """Create a new asset disposal request (employees only)"""
    model = AssetDisposal
    form_class = AssetDisposalForm
    template_name = 'assets/disposal_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.requested_by = self.request.user
        messages.success(self.request, 'Asset disposal request submitted successfully')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('disposal-detail', kwargs={'pk': self.object.pk})


class AssetDisposalDetailView(LoginRequiredMixin, DetailView):
    """View details of an asset disposal request"""
    model = AssetDisposal
    template_name = 'assets/disposal_detail.html'
    context_object_name = 'disposal'
    
    def get_queryset(self):
        org = self.request.user.organization
        qs = AssetDisposal.objects.filter(organization=org).select_related(
            'asset', 'requested_by', 'approved_by'
        )
        
        # Employees can view only their own disposals
        user = self.request.user
        if user.role == user.Role.EMPLOYEE:
            qs = qs.filter(requested_by=user)
        
        return qs


class AssetDisposalManagerApproveView(LoginRequiredMixin, UpdateView):
    """Manager approval of asset disposal request (step 1)"""
    model = AssetDisposal
    form_class = AssetDisposalManagerApprovalForm
    template_name = 'assets/disposal_manager_approve.html'
    
    def test_func(self):
        """Only managers/senior managers can approve disposals first"""
        return self.request.user.role in [
            self.request.user.Role.SENIOR_MANAGER,
            self.request.user.Role.CHECKER
        ]
    
    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, 'You do not have permission to review disposal requests.')
            return redirect('disposal-list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        org = self.request.user.organization
        return AssetDisposal.objects.filter(organization=org, status=AssetDisposal.Status.PENDING)
    
    def form_valid(self, form):
        form.instance.manager_approved_by = self.request.user
        form.instance.manager_approved_at = datetime.now()
        
        if form.instance.status == AssetDisposal.Status.MANAGER_APPROVED:
            messages.success(self.request, f'Asset disposal request approved by manager: {form.instance.asset.asset_tag}. Pending admin approval.')
        elif form.instance.status == AssetDisposal.Status.REJECTED:
            messages.warning(self.request, f'Asset disposal request rejected by manager: {form.instance.asset.asset_tag}')
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('disposal-detail', kwargs={'pk': self.object.pk})


class AssetDisposalApproveView(LoginRequiredMixin, UpdateView):
    """Final admin approval of asset disposal request (step 2)"""
    model = AssetDisposal
    form_class = AssetDisposalApprovalForm
    template_name = 'assets/disposal_approve.html'
    
    def test_func(self):
        """Only admins can give final approval"""
        return self.request.user.is_superuser or self.request.user.role == self.request.user.Role.ADMIN
    
    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, 'You do not have permission to approve disposal requests.')
            return redirect('disposal-list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        org = self.request.user.organization
        return AssetDisposal.objects.filter(organization=org, status=AssetDisposal.Status.MANAGER_APPROVED)
    
    def form_valid(self, form):
        form.instance.approved_by = self.request.user
        form.instance.approved_at = datetime.now()
        
        if form.instance.status == AssetDisposal.Status.APPROVED:
            messages.success(self.request, f'Asset disposal request approved: {form.instance.asset.asset_tag}')
        elif form.instance.status == AssetDisposal.Status.REJECTED:
            messages.warning(self.request, f'Asset disposal request rejected: {form.instance.asset.asset_tag}')
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('disposal-detail', kwargs={'pk': self.object.pk})


# --- DEPRECIATION REPORT VIEWS ---
class DepreciationReportView(LoginRequiredMixin, ListView):
    """Comprehensive depreciation report — all assets with individual depreciation details"""
    model = Asset
    template_name = 'assets/depreciation_report_all.html'
    context_object_name = 'assets'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and user.role == user.Role.EMPLOYEE and not user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset

        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False,
            purchase_price__isnull=False,
            purchase_price__gt=0,
        ).select_related('category', 'department', 'location', 'group').only(
            'id', 'name', 'asset_tag', 'asset_code', 'serial_number',
            'purchase_price', 'purchase_date', 'useful_life_years',
            'salvage_value', 'depreciation_method', 'expected_units',
            'units_consumed', 'status',
            'category_id', 'category__name',
            'department_id', 'department__name',
            'location_id', 'location__name',
            'group_id', 'group__name',
            'organization_id', 'is_deleted',
            'cached_accumulated_depreciation', 'cached_nbv',
        )

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
                Q(asset_code__icontains=query) |
                Q(serial_number__icontains=query) |
                Q(category__name__icontains=query) |
                Q(department__name__icontains=query)
            )

        self._opening_date = None
        self._closing_date = None
        depr_date_from = self.request.GET.get('depr_date_from')
        depr_date_to = self.request.GET.get('depr_date_to')

        if depr_date_from:
            try:
                self._opening_date = datetime.strptime(depr_date_from, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if depr_date_to:
            try:
                self._closing_date = datetime.strptime(depr_date_to, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if self._closing_date:
            queryset = queryset.filter(Q(purchase_date__lte=self._closing_date) | Q(purchase_date__isnull=True))

        depr_filters = {
            'depr_category': 'category_id',
            'depr_group': 'group_id',
            'depr_department': 'department_id',
            'depr_site': 'site_id',
            'depr_branch': 'branch_id',
            'depr_building': 'building_id',
            'depr_location': 'location_id',
        }
        for param, field in depr_filters.items():
            val = self.request.GET.get(param)
            if val:
                queryset = queryset.filter(**{field: val})

        self._cached_queryset = queryset.order_by('-purchase_date')
        return self._cached_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        qs = self.get_queryset()

        from django.db.models import Sum, Count
        from django.db.models.functions import Coalesce

        opening_date = getattr(self, '_opening_date', None)
        closing_date = getattr(self, '_closing_date', None)

        agg = qs.aggregate(
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_count=Count('id'),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        )
        total_cost = agg['total_cost']
        total_count = agg['total_count']
        total_acc_dep = agg['total_acc_dep']
        total_nbv = agg['total_nbv']

        if opening_date or closing_date:
            total_opening_value = Decimal('0')
            total_closing_value = Decimal('0')
            for asset in qs.iterator(chunk_size=2000):
                total_opening_value += asset.get_value_at_date(opening_date) if opening_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
                total_closing_value += asset.get_value_at_date(closing_date) if closing_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
        else:
            total_opening_value = total_nbv
            total_closing_value = total_nbv

        context['total_cost'] = total_cost
        context['total_acc_dep'] = total_acc_dep
        context['total_nbv'] = total_nbv
        context['total_assets_report'] = total_count
        context['total_opening_value'] = total_opening_value
        context['total_closing_value'] = total_closing_value
        context['period_depreciation'] = total_opening_value - total_closing_value
        context['opening_date'] = opening_date
        context['closing_date'] = closing_date

        context['categories'] = Category.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['departments'] = Department.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['locations'] = Location.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['branches'] = Branch.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['sites'] = Site.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['buildings'] = Building.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['groups'] = Group.objects.filter(organization=org).only('id', 'name').order_by('name')

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()

        context['depr_date_from'] = self.request.GET.get('depr_date_from', '')
        context['depr_date_to'] = self.request.GET.get('depr_date_to', '')
        context['depr_category'] = self.request.GET.get('depr_category', '')
        context['depr_group'] = self.request.GET.get('depr_group', '')
        context['depr_department'] = self.request.GET.get('depr_department', '')
        context['depr_site'] = self.request.GET.get('depr_site', '')
        context['depr_branch'] = self.request.GET.get('depr_branch', '')
        context['depr_building'] = self.request.GET.get('depr_building', '')
        context['depr_location'] = self.request.GET.get('depr_location', '')
        context['search_query'] = self.request.GET.get('q', '')

        if context.get('page_obj'):
            enriched_assets = []
            for asset in context['page_obj'].object_list:
                asset.opening_value = asset.get_value_at_date(opening_date) if opening_date else asset.current_value
                asset.closing_value = asset.get_value_at_date(closing_date) if closing_date else asset.current_value
                asset.period_depreciation = asset.opening_value - asset.closing_value
                enriched_assets.append(asset)
            context['assets'] = enriched_assets

        return context


class DepreciationReportCategoryView(LoginRequiredMixin, ListView):
    """Dedicated view for category-based depreciation report"""
    model = Asset
    template_name = 'assets/depreciation_report_category.html'
    context_object_name = 'assets'
    paginate_by = 50

    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset

        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False,
            purchase_price__isnull=False,
            purchase_price__gt=0,
        ).select_related('category').only(
            'id', 'name', 'asset_tag', 'asset_code', 'serial_number',
            'purchase_price', 'purchase_date', 'useful_life_years',
            'salvage_value', 'depreciation_method', 'expected_units',
            'units_consumed', 'category_id', 'category__name',
            'organization_id', 'is_deleted', 'status',
            'cached_accumulated_depreciation', 'cached_nbv',
        )

        # Search filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
                Q(asset_code__icontains=query) |
                Q(serial_number__icontains=query) |
                Q(category__name__icontains=query)
            )

        # Date range filters
        self._opening_date = None
        self._closing_date = None
        depr_date_from = self.request.GET.get('depr_date_from')
        depr_date_to = self.request.GET.get('depr_date_to')

        if depr_date_from:
            try:
                self._opening_date = datetime.strptime(depr_date_from, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if depr_date_to:
            try:
                self._closing_date = datetime.strptime(depr_date_to, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if self._closing_date:
            queryset = queryset.filter(Q(purchase_date__lte=self._closing_date) | Q(purchase_date__isnull=True))

        # Dimension filters
        depr_filters = {
            'depr_category': 'category_id',
            'depr_group': 'group_id',
            'depr_department': 'department_id',
            'depr_site': 'site_id',
            'depr_branch': 'branch_id',
            'depr_building': 'building_id',
            'depr_location': 'location_id',
        }
        for param, field in depr_filters.items():
            val = self.request.GET.get(param)
            if val:
                queryset = queryset.filter(**{field: val})

        self._cached_queryset = queryset.order_by('-purchase_date')
        return self._cached_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        qs = self.get_queryset()

        from django.db.models import Sum, Count
        from django.db.models.functions import Coalesce

        opening_date = getattr(self, '_opening_date', None)
        closing_date = getattr(self, '_closing_date', None)

        # ── Fast path: DB-level aggregation using cached fields ──
        agg = qs.aggregate(
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_count=Count('id'),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        )
        total_cost = agg['total_cost']
        total_count = agg['total_count']
        total_acc_dep = agg['total_acc_dep']
        total_nbv = agg['total_nbv']

        # Category grouping via DB aggregation
        grouped_qs = qs.values('category', 'category__name').annotate(
            count=Count('id'),
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        ).order_by('-total_cost')[:100]

        grouped_list = []
        for g in grouped_qs:
            grouped_list.append({
                'id': g['category'],
                'name': g['category__name'] or 'Uncategorized',
                'total_cost': g['total_cost'],
                'total_acc_dep': g['total_acc_dep'],
                'total_nbv': g['total_nbv'],
                'count': g['count'],
            })

        # ── Period values: only iterate if date range specified ──
        if opening_date or closing_date:
            total_opening_value = Decimal('0')
            total_closing_value = Decimal('0')
            for asset in qs.iterator(chunk_size=2000):
                total_opening_value += asset.get_value_at_date(opening_date) if opening_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
                total_closing_value += asset.get_value_at_date(closing_date) if closing_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
        else:
            total_opening_value = total_nbv
            total_closing_value = total_nbv

        context['total_cost'] = total_cost
        context['total_acc_dep'] = total_acc_dep
        context['total_nbv'] = total_nbv
        context['total_assets_report'] = total_count
        context['total_opening_value'] = total_opening_value
        context['total_closing_value'] = total_closing_value
        context['period_depreciation'] = total_opening_value - total_closing_value
        context['opening_date'] = opening_date
        context['closing_date'] = closing_date
        context['grouped_data'] = grouped_list

        context['categories'] = Category.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['departments'] = Department.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['locations'] = Location.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['branches'] = Branch.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['sites'] = Site.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['buildings'] = Building.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['groups'] = Group.objects.filter(organization=org).only('id', 'name').order_by('name')
        
        # Filter persistence
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()
        
        # Store filter values
        context['depr_date_from'] = self.request.GET.get('depr_date_from', '')
        context['depr_date_to'] = self.request.GET.get('depr_date_to', '')
        context['depr_category'] = self.request.GET.get('depr_category', '')
        context['depr_group'] = self.request.GET.get('depr_group', '')
        context['depr_department'] = self.request.GET.get('depr_department', '')
        context['depr_site'] = self.request.GET.get('depr_site', '')
        context['depr_branch'] = self.request.GET.get('depr_branch', '')
        context['depr_building'] = self.request.GET.get('depr_building', '')
        context['depr_location'] = self.request.GET.get('depr_location', '')
        context['search_query'] = self.request.GET.get('q', '')

        # Enrich paginated assets with opening/closing values
        if context.get('page_obj'):
            enriched_assets = []
            for asset in context['page_obj'].object_list:
                asset.opening_value = asset.get_value_at_date(opening_date) if opening_date else asset.current_value
                asset.closing_value = asset.get_value_at_date(closing_date) if closing_date else asset.current_value
                asset.period_depreciation = asset.opening_value - asset.closing_value
                enriched_assets.append(asset)
            context['assets'] = enriched_assets
        
        return context


class DepreciationReportDepartmentView(LoginRequiredMixin, ListView):
    """Dedicated view for department-based depreciation report"""
    model = Asset
    template_name = 'assets/depreciation_report_department.html'
    context_object_name = 'assets'
    paginate_by = 50

    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset

        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False,
            purchase_price__isnull=False,
            purchase_price__gt=0,
        ).select_related('department').only(
            'id', 'name', 'asset_tag', 'asset_code', 'serial_number',
            'purchase_price', 'purchase_date', 'useful_life_years',
            'salvage_value', 'depreciation_method', 'expected_units',
            'units_consumed', 'department_id', 'department__name',
            'organization_id', 'is_deleted', 'status',
            'cached_accumulated_depreciation', 'cached_nbv',
        )

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
                Q(asset_code__icontains=query) |
                Q(serial_number__icontains=query) |
                Q(department__name__icontains=query)
            )

        self._opening_date = None
        self._closing_date = None
        depr_date_from = self.request.GET.get('depr_date_from')
        depr_date_to = self.request.GET.get('depr_date_to')

        if depr_date_from:
            try:
                self._opening_date = datetime.strptime(depr_date_from, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if depr_date_to:
            try:
                self._closing_date = datetime.strptime(depr_date_to, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if self._closing_date:
            queryset = queryset.filter(Q(purchase_date__lte=self._closing_date) | Q(purchase_date__isnull=True))

        depr_filters = {
            'depr_category': 'category_id',
            'depr_group': 'group_id',
            'depr_department': 'department_id',
            'depr_site': 'site_id',
            'depr_branch': 'branch_id',
            'depr_building': 'building_id',
            'depr_location': 'location_id',
        }
        for param, field in depr_filters.items():
            val = self.request.GET.get(param)
            if val:
                queryset = queryset.filter(**{field: val})

        self._cached_queryset = queryset.order_by('-purchase_date')
        return self._cached_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        qs = self.get_queryset()

        from django.db.models import Sum, Count
        from django.db.models.functions import Coalesce

        opening_date = getattr(self, '_opening_date', None)
        closing_date = getattr(self, '_closing_date', None)

        # ── Fast path: DB-level aggregation using cached fields ──
        agg = qs.aggregate(
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_count=Count('id'),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        )
        total_cost = agg['total_cost']
        total_count = agg['total_count']
        total_acc_dep = agg['total_acc_dep']
        total_nbv = agg['total_nbv']

        # Department grouping via DB aggregation
        grouped_qs = qs.values('department', 'department__name').annotate(
            count=Count('id'),
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        ).order_by('-total_cost')[:100]

        grouped_list = []
        for g in grouped_qs:
            grouped_list.append({
                'id': g['department'],
                'name': g['department__name'] or 'Uncategorized',
                'total_cost': g['total_cost'],
                'total_acc_dep': g['total_acc_dep'],
                'total_nbv': g['total_nbv'],
                'count': g['count'],
            })

        # ── Period values: only iterate if date range specified ──
        if opening_date or closing_date:
            total_opening_value = Decimal('0')
            total_closing_value = Decimal('0')
            for asset in qs.iterator(chunk_size=2000):
                total_opening_value += asset.get_value_at_date(opening_date) if opening_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
                total_closing_value += asset.get_value_at_date(closing_date) if closing_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
        else:
            total_opening_value = total_nbv
            total_closing_value = total_nbv

        context['total_cost'] = total_cost
        context['total_acc_dep'] = total_acc_dep
        context['total_nbv'] = total_nbv
        context['total_assets_report'] = total_count
        context['total_opening_value'] = total_opening_value
        context['total_closing_value'] = total_closing_value
        context['period_depreciation'] = total_opening_value - total_closing_value
        context['opening_date'] = opening_date
        context['closing_date'] = closing_date
        context['grouped_data'] = grouped_list

        context['categories'] = Category.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['departments'] = Department.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['locations'] = Location.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['branches'] = Branch.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['sites'] = Site.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['buildings'] = Building.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['groups'] = Group.objects.filter(organization=org).only('id', 'name').order_by('name')

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()

        context['depr_date_from'] = self.request.GET.get('depr_date_from', '')
        context['depr_date_to'] = self.request.GET.get('depr_date_to', '')
        context['depr_category'] = self.request.GET.get('depr_category', '')
        context['depr_group'] = self.request.GET.get('depr_group', '')
        context['depr_department'] = self.request.GET.get('depr_department', '')
        context['depr_site'] = self.request.GET.get('depr_site', '')
        context['depr_branch'] = self.request.GET.get('depr_branch', '')
        context['depr_building'] = self.request.GET.get('depr_building', '')
        context['depr_location'] = self.request.GET.get('depr_location', '')
        context['search_query'] = self.request.GET.get('q', '')

        if context.get('page_obj'):
            enriched_assets = []
            for asset in context['page_obj'].object_list:
                asset.opening_value = asset.get_value_at_date(opening_date) if opening_date else asset.current_value
                asset.closing_value = asset.get_value_at_date(closing_date) if closing_date else asset.current_value
                asset.period_depreciation = asset.opening_value - asset.closing_value
                enriched_assets.append(asset)
            context['assets'] = enriched_assets

        return context

class DepreciationReportLocationView(LoginRequiredMixin, ListView):
    """Dedicated view for location-based depreciation report"""
    model = Asset
    template_name = 'assets/depreciation_report_location.html'
    context_object_name = 'assets'
    paginate_by = 50

    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset

        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False,
            purchase_price__isnull=False,
            purchase_price__gt=0,
        ).select_related('location').only(
            'id', 'name', 'asset_tag', 'asset_code', 'serial_number',
            'purchase_price', 'purchase_date', 'useful_life_years',
            'salvage_value', 'depreciation_method', 'expected_units',
            'units_consumed', 'location_id', 'location__name',
            'organization_id', 'is_deleted', 'status',
            'cached_accumulated_depreciation', 'cached_nbv',
        )

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
                Q(asset_code__icontains=query) |
                Q(serial_number__icontains=query) |
                Q(location__name__icontains=query)
            )

        self._opening_date = None
        self._closing_date = None
        depr_date_from = self.request.GET.get('depr_date_from')
        depr_date_to = self.request.GET.get('depr_date_to')

        if depr_date_from:
            try:
                self._opening_date = datetime.strptime(depr_date_from, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if depr_date_to:
            try:
                self._closing_date = datetime.strptime(depr_date_to, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if self._closing_date:
            queryset = queryset.filter(Q(purchase_date__lte=self._closing_date) | Q(purchase_date__isnull=True))

        depr_filters = {
            'depr_category': 'category_id',
            'depr_group': 'group_id',
            'depr_department': 'department_id',
            'depr_site': 'site_id',
            'depr_branch': 'branch_id',
            'depr_building': 'building_id',
            'depr_location': 'location_id',
        }
        for param, field in depr_filters.items():
            val = self.request.GET.get(param)
            if val:
                queryset = queryset.filter(**{field: val})

        self._cached_queryset = queryset.order_by('-purchase_date')
        return self._cached_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        qs = self.get_queryset()

        from django.db.models import Sum, Count
        from django.db.models.functions import Coalesce

        opening_date = getattr(self, '_opening_date', None)
        closing_date = getattr(self, '_closing_date', None)

        # ── Fast path: DB-level aggregation using cached fields ──
        agg = qs.aggregate(
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_count=Count('id'),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        )
        total_cost = agg['total_cost']
        total_count = agg['total_count']
        total_acc_dep = agg['total_acc_dep']
        total_nbv = agg['total_nbv']

        # Location grouping via DB aggregation
        grouped_qs = qs.values('location', 'location__name').annotate(
            count=Count('id'),
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        ).order_by('-total_cost')[:100]

        grouped_list = []
        for g in grouped_qs:
            grouped_list.append({
                'id': g['location'],
                'name': g['location__name'] or 'Uncategorized',
                'total_cost': g['total_cost'],
                'total_acc_dep': g['total_acc_dep'],
                'total_nbv': g['total_nbv'],
                'count': g['count'],
            })

        # ── Period values: only iterate if date range specified ──
        if opening_date or closing_date:
            total_opening_value = Decimal('0')
            total_closing_value = Decimal('0')
            for asset in qs.iterator(chunk_size=2000):
                total_opening_value += asset.get_value_at_date(opening_date) if opening_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
                total_closing_value += asset.get_value_at_date(closing_date) if closing_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
        else:
            total_opening_value = total_nbv
            total_closing_value = total_nbv

        context['total_cost'] = total_cost
        context['total_acc_dep'] = total_acc_dep
        context['total_nbv'] = total_nbv
        context['total_assets_report'] = total_count
        context['total_opening_value'] = total_opening_value
        context['total_closing_value'] = total_closing_value
        context['period_depreciation'] = total_opening_value - total_closing_value
        context['opening_date'] = opening_date
        context['closing_date'] = closing_date
        context['grouped_data'] = grouped_list

        context['categories'] = Category.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['departments'] = Department.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['locations'] = Location.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['branches'] = Branch.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['sites'] = Site.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['buildings'] = Building.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['groups'] = Group.objects.filter(organization=org).only('id', 'name').order_by('name')

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()

        context['depr_date_from'] = self.request.GET.get('depr_date_from', '')
        context['depr_date_to'] = self.request.GET.get('depr_date_to', '')
        context['depr_category'] = self.request.GET.get('depr_category', '')
        context['depr_group'] = self.request.GET.get('depr_group', '')
        context['depr_department'] = self.request.GET.get('depr_department', '')
        context['depr_site'] = self.request.GET.get('depr_site', '')
        context['depr_branch'] = self.request.GET.get('depr_branch', '')
        context['depr_building'] = self.request.GET.get('depr_building', '')
        context['depr_location'] = self.request.GET.get('depr_location', '')
        context['search_query'] = self.request.GET.get('q', '')

        if context.get('page_obj'):
            enriched_assets = []
            for asset in context['page_obj'].object_list:
                asset.opening_value = asset.get_value_at_date(opening_date) if opening_date else asset.current_value
                asset.closing_value = asset.get_value_at_date(closing_date) if closing_date else asset.current_value
                asset.period_depreciation = asset.opening_value - asset.closing_value
                enriched_assets.append(asset)
            context['assets'] = enriched_assets

        return context

class DepreciationReportGroupView(LoginRequiredMixin, ListView):
    """Dedicated view for group-based depreciation report"""
    model = Asset
    template_name = 'assets/depreciation_report_group.html'
    context_object_name = 'assets'
    paginate_by = 50

    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset

        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False,
            purchase_price__isnull=False,
            purchase_price__gt=0,
        ).select_related('group').only(
            'id', 'name', 'asset_tag', 'asset_code', 'serial_number',
            'purchase_price', 'purchase_date', 'useful_life_years',
            'salvage_value', 'depreciation_method', 'expected_units',
            'units_consumed', 'group_id', 'group__name',
            'organization_id', 'is_deleted', 'status',
            'cached_accumulated_depreciation', 'cached_nbv',
        )

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
                Q(asset_code__icontains=query) |
                Q(serial_number__icontains=query) |
                Q(group__name__icontains=query)
            )

        self._opening_date = None
        self._closing_date = None
        depr_date_from = self.request.GET.get('depr_date_from')
        depr_date_to = self.request.GET.get('depr_date_to')

        if depr_date_from:
            try:
                self._opening_date = datetime.strptime(depr_date_from, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if depr_date_to:
            try:
                self._closing_date = datetime.strptime(depr_date_to, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        if self._closing_date:
            queryset = queryset.filter(Q(purchase_date__lte=self._closing_date) | Q(purchase_date__isnull=True))

        depr_filters = {
            'depr_category': 'category_id',
            'depr_group': 'group_id',
            'depr_department': 'department_id',
            'depr_site': 'site_id',
            'depr_branch': 'branch_id',
            'depr_building': 'building_id',
            'depr_location': 'location_id',
        }
        for param, field in depr_filters.items():
            val = self.request.GET.get(param)
            if val:
                queryset = queryset.filter(**{field: val})

        self._cached_queryset = queryset.order_by('-purchase_date')
        return self._cached_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        qs = self.get_queryset()

        from django.db.models import Sum, Count
        from django.db.models.functions import Coalesce

        opening_date = getattr(self, '_opening_date', None)
        closing_date = getattr(self, '_closing_date', None)

        # ── Fast path: DB-level aggregation using cached fields ──
        agg = qs.aggregate(
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_count=Count('id'),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        )
        total_cost = agg['total_cost']
        total_count = agg['total_count']
        total_acc_dep = agg['total_acc_dep']
        total_nbv = agg['total_nbv']

        # Group grouping via DB aggregation
        grouped_qs = qs.values('group', 'group__name').annotate(
            count=Count('id'),
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_acc_dep=Coalesce(Sum('cached_accumulated_depreciation'), Decimal('0')),
            total_nbv=Coalesce(Sum('cached_nbv'), Decimal('0')),
        ).order_by('-total_cost')[:100]

        grouped_list = []
        for g in grouped_qs:
            grouped_list.append({
                'id': g['group'],
                'name': g['group__name'] or 'Uncategorized',
                'total_cost': g['total_cost'],
                'total_acc_dep': g['total_acc_dep'],
                'total_nbv': g['total_nbv'],
                'count': g['count'],
            })

        # ── Period values: only iterate if date range specified ──
        if opening_date or closing_date:
            total_opening_value = Decimal('0')
            total_closing_value = Decimal('0')
            for asset in qs.iterator(chunk_size=2000):
                total_opening_value += asset.get_value_at_date(opening_date) if opening_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
                total_closing_value += asset.get_value_at_date(closing_date) if closing_date else (asset.purchase_price - asset.cached_accumulated_depreciation)
        else:
            total_opening_value = total_nbv
            total_closing_value = total_nbv

        context['total_cost'] = total_cost
        context['total_acc_dep'] = total_acc_dep
        context['total_nbv'] = total_nbv
        context['total_assets_report'] = total_count
        context['total_opening_value'] = total_opening_value
        context['total_closing_value'] = total_closing_value
        context['period_depreciation'] = total_opening_value - total_closing_value
        context['opening_date'] = opening_date
        context['closing_date'] = closing_date
        context['grouped_data'] = grouped_list

        context['categories'] = Category.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['departments'] = Department.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['locations'] = Location.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['branches'] = Branch.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['sites'] = Site.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['buildings'] = Building.objects.filter(organization=org).only('id', 'name').order_by('name')
        context['groups'] = Group.objects.filter(organization=org).only('id', 'name').order_by('name')

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()

        context['depr_date_from'] = self.request.GET.get('depr_date_from', '')
        context['depr_date_to'] = self.request.GET.get('depr_date_to', '')
        context['depr_category'] = self.request.GET.get('depr_category', '')
        context['depr_group'] = self.request.GET.get('depr_group', '')
        context['depr_department'] = self.request.GET.get('depr_department', '')
        context['depr_site'] = self.request.GET.get('depr_site', '')
        context['depr_branch'] = self.request.GET.get('depr_branch', '')
        context['depr_building'] = self.request.GET.get('depr_building', '')
        context['depr_location'] = self.request.GET.get('depr_location', '')
        context['search_query'] = self.request.GET.get('q', '')

        if context.get('page_obj'):
            enriched_assets = []
            for asset in context['page_obj'].object_list:
                asset.opening_value = asset.get_value_at_date(opening_date) if opening_date else asset.current_value
                asset.closing_value = asset.get_value_at_date(closing_date) if closing_date else asset.current_value
                asset.period_depreciation = asset.opening_value - asset.closing_value
                enriched_assets.append(asset)
            context['assets'] = enriched_assets

        return context

# AJAX View to create category inline
@login_required
def ajax_create_category(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            useful_life_years = request.POST.get('useful_life_years', '5')
            depreciation_method = request.POST.get('depreciation_method', 'straight_line')
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Category name is required'}, status=400)
            
            # Check if category already exists
            if Category.objects.filter(organization=request.user.organization, name__iexact=name).exists():
                return JsonResponse({'success': False, 'error': 'Category with this name already exists'}, status=400)
            
            category = Category.objects.create(
                organization=request.user.organization,
                name=name,
                useful_life_years=int(useful_life_years),
                depreciation_method=depreciation_method
            )
            
            return JsonResponse({
                'success': True,
                'id': category.id,
                'name': category.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


# AJAX View to create subcategory inline
@login_required
def ajax_create_subcategory(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            category_id = request.POST.get('category_id', '')
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Subcategory name is required'}, status=400)
            
            if not category_id:
                return JsonResponse({'success': False, 'error': 'Category is required'}, status=400)
            
            # Get category and verify it belongs to user's organization
            try:
                category = Category.objects.get(id=category_id, organization=request.user.organization)
            except Category.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid category'}, status=400)
            
            # Check if subcategory already exists
            if SubCategory.objects.filter(category=category, name__iexact=name).exists():
                return JsonResponse({'success': False, 'error': 'Subcategory with this name already exists in this category'}, status=400)
            
            subcategory = SubCategory.objects.create(
                category=category,
                name=name
            )
            
            return JsonResponse({
                'success': True,
                'id': subcategory.id,
                'name': subcategory.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

# Barcode & QR Code Views
@login_required
def generate_asset_codes(request, pk):
    """Generate or regenerate barcode/QR/label for an asset."""
    try:
        asset = Asset.objects.get(id=pk, organization=request.user.organization)
        from .code_generators import AssetCodeGenerator
        
        barcode_path = AssetCodeGenerator.save_barcode_to_file(asset.asset_tag)
        qr_path = AssetCodeGenerator.save_qr_to_file(asset.asset_tag)
        label_path = AssetCodeGenerator.save_label_to_file(asset.asset_tag)
        
        asset.barcode_image = barcode_path
        asset.qr_code_image = qr_path
        asset.label_image = label_path
        asset.save(update_fields=['barcode_image', 'qr_code_image', 'label_image'])
        
        return JsonResponse({
            'success': True,
            'barcode_url': asset.barcode_image.url if asset.barcode_image else None,
            'qr_url': asset.qr_code_image.url if asset.qr_code_image else None,
            'label_url': asset.label_image.url if asset.label_image else None,
        })
    except Asset.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Asset not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def download_asset_barcode(request, pk):
    """Download barcode image for asset"""
    try:
        asset = Asset.objects.get(id=pk, organization=request.user.organization)
        if not asset.barcode_image:
            from .code_generators import AssetCodeGenerator
            path = AssetCodeGenerator.save_barcode_to_file(asset.asset_tag)
            if path:
                asset.barcode_image = path
                asset.save(update_fields=['barcode_image'])
        
        if asset.barcode_image:
            return redirect(asset.barcode_image.url)
        return JsonResponse({'error': 'No barcode available'}, status=404)
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)


@login_required
def download_asset_qr(request, pk):
    """Download QR code image for asset"""
    try:
        asset = Asset.objects.get(id=pk, organization=request.user.organization)
        if not asset.qr_code_image:
            from .code_generators import AssetCodeGenerator
            path = AssetCodeGenerator.save_qr_to_file(asset.asset_tag)
            if path:
                asset.qr_code_image = path
                asset.save(update_fields=['qr_code_image'])
        
        if asset.qr_code_image:
            return redirect(asset.qr_code_image.url)
        return JsonResponse({'error': 'No QR code available'}, status=404)
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)


@login_required
def download_asset_label(request, pk):
    """Download combined label image for asset"""
    try:
        asset = Asset.objects.get(id=pk, organization=request.user.organization)
        if not asset.label_image:
            from .code_generators import AssetCodeGenerator
            path = AssetCodeGenerator.save_label_to_file(asset.asset_tag)
            if path:
                asset.label_image = path
                asset.save(update_fields=['label_image'])
        
        if asset.label_image:
            return redirect(asset.label_image.url)
        return JsonResponse({'error': 'No label available'}, status=404)
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)


@login_required
def download_barcode_batch(request):
    """Download barcodes for multiple assets as ZIP."""
    import tempfile
    import zipfile
    from pathlib import Path
    from django.http import FileResponse
    
    try:
        asset_ids = request.GET.get('asset_ids', '').split(',')
        if not asset_ids or not asset_ids[0]:
            return JsonResponse({'error': 'No assets specified'}, status=400)
        
        assets = Asset.objects.filter(
            id__in=asset_ids,
            organization=request.user.organization
        )
        
        if not assets.exists():
            return JsonResponse({'error': 'No assets found'}, status=404)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
                for asset in assets:
                    if asset.barcode_image:
                        barcode_path = Path(asset.barcode_image.path)
                        if barcode_path.exists():
                            zf.write(barcode_path, arcname=f'{asset.asset_tag}_barcode.png')
            tmp_path = tmp.name
        
        response = FileResponse(
            open(tmp_path, 'rb'),
            content_type='application/zip'
        )
        response['Content-Disposition'] = f'attachment; filename=\"asset_barcodes_{request.user.organization.code}.zip\"'
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def print_asset_label(request, pk):
    """Render a browser-printable label page for a single asset."""
    asset = get_object_or_404(Asset, id=pk, organization=request.user.organization)
    org = request.user.organization
    design = request.GET.get('design', getattr(org, 'label_template', 'CLASSIC'))
    designs = org.LabelTemplate.choices if hasattr(org, 'LabelTemplate') else []
    return render(request, 'assets/print_label.html', {
        'assets': [asset],
        'design': design,
        'designs': designs,
        'org': org,
    })


@login_required
def label_print_center(request):
    """Dedicated page for bulk label printing with design selection and filters."""
    org = request.user.organization
    all_assets = Asset.objects.filter(
        organization=org
    ).order_by('asset_tag').values_list('asset_tag', flat=True)
    # Build lightweight asset list for dropdowns
    asset_tags = [{'asset_tag': tag} for tag in all_assets]
    categories = Category.objects.filter(organization=org).order_by('name')
    branches = Branch.objects.filter(organization=org).order_by('name')

    return render(request, 'assets/label_print_center.html', {
        'org': org,
        'all_assets': asset_tags,
        'categories': categories,
        'branches': branches,
    })


@login_required
def print_asset_labels_bulk(request):
    """Render a browser-printable label page for multiple assets.
    
    Supports multiple selection modes:
    - ids: comma-separated asset UUIDs
    - tag_from + tag_to: tag range (inclusive)
    - category / branch: filter by category or branch
    - specific_tags: comma/newline-separated tags
    """
    org = request.user.organization
    design = request.GET.get('design', getattr(org, 'label_template', 'CLASSIC'))
    designs = org.LabelTemplate.choices if hasattr(org, 'LabelTemplate') else []

    assets = Asset.objects.none()

    # Mode 1: By IDs (existing behavior)
    asset_ids = request.GET.get('ids', '').split(',')
    asset_ids = [aid.strip() for aid in asset_ids if aid.strip()]

    if asset_ids:
        assets = Asset.objects.filter(id__in=asset_ids, organization=org)

    # Mode 2: By tag range
    elif request.GET.get('tag_from') and request.GET.get('tag_to'):
        tag_from = request.GET['tag_from'].strip()
        tag_to = request.GET['tag_to'].strip()
        assets = Asset.objects.filter(
            organization=org,
            asset_tag__gte=tag_from,
            asset_tag__lte=tag_to,
        ).order_by('asset_tag')

    # Mode 3: By category/branch filters
    elif request.GET.get('category') or request.GET.get('branch'):
        qs = Asset.objects.filter(organization=org)
        if request.GET.get('category'):
            qs = qs.filter(category_id=request.GET['category'])
        if request.GET.get('branch'):
            qs = qs.filter(branch_id=request.GET['branch'])
        assets = qs.order_by('asset_tag')

    # Mode 4: Specific tags
    elif request.GET.get('specific_tags'):
        raw_tags = request.GET['specific_tags']
        # Split by comma or newline
        tags = [t.strip() for t in raw_tags.replace('\n', ',').split(',') if t.strip()]
        assets = Asset.objects.filter(organization=org, asset_tag__in=tags).order_by('asset_tag')

    if not assets.exists():
        return render(request, 'assets/print_label.html', {
            'assets': [],
            'design': design,
            'designs': designs,
            'org': org,
        })

    # Batch pagination - max 1000 labels per page
    BATCH_SIZE = 1000
    total_count = assets.count()
    batch = int(request.GET.get('batch', 1))
    total_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE  # ceil division
    offset = (batch - 1) * BATCH_SIZE
    assets_batch = assets[offset:offset + BATCH_SIZE]

    assets_batch = assets_batch.select_related('category', 'location', 'company')

    # Auto-generate missing barcode/QR codes before printing
    from .code_generators import generate_codes_for_asset
    for asset in assets_batch:
        if asset.asset_tag and (not asset.barcode_image or not asset.qr_code_image):
            try:
                generate_codes_for_asset(asset)
            except Exception:
                pass

    # Build next/prev batch URLs
    remaining = total_count - (offset + BATCH_SIZE)
    if remaining < 0:
        remaining = 0

    return render(request, 'assets/print_label.html', {
        'assets': assets_batch,
        'design': design,
        'designs': designs,
        'org': org,
        'batch': batch,
        'total_batches': total_batches,
        'total_count': total_count,
        'batch_size': BATCH_SIZE,
        'remaining': remaining,
        'batch_start': offset + 1,
        'batch_end': min(offset + BATCH_SIZE, total_count),
    })
