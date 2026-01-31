from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
import csv
import io
from .models import Asset, AssetAttachment, Category, SubCategory, Vendor, generate_asset_tag
from .forms import AssetForm, CategoryForm, SubCategoryForm, VendorForm, AssetImportForm
from django.db import transaction
from apps.locations.models import Branch, Building, Floor, Room
from django.urls import reverse
from django.http import HttpResponse, JsonResponse

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
    return JsonResponse([], safe=False)

def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_assets.csv"'

    writer = csv.writer(response)
    # Header
    writer.writerow([
        'name', 'asset_tag', 'category_code', 'status', 'purchase_price',
        'brand', 'model', 'serial_number', 'notes',
        'branch', 'building', 'floor', 'room', 'vendor'
    ])
    # Sample Row 1 - with custom asset tag
    writer.writerow([
        'MacBook Pro 16', 'CUSTOM-001', 'IT', 'ACTIVE', '2499.00', 
        'Apple', 'M3 Pro', 'SN12345678', 'Assigned to Design Team',
        'Main Branch', 'HQ Building', '2nd Floor', 'Office 204', 'TechStore Inc.'
    ])
    # Sample Row 2 - asset tag will be auto-generated (AST-00001, AST-00002, etc.)
    writer.writerow([
        'Office Chair', '', 'FUR', 'IN_STORAGE', '150.00',
        'Herman Miller', 'Aeron', '', '',
        'Main Branch', 'HQ Building', '1st Floor', 'Storage Room B', ''
    ])
    
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
        ).select_related('category', 'branch', 'assigned_to')

        # Search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(asset_tag__icontains=query) |
                Q(serial_number__icontains=query)
            )
            
        # Filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('view') == 'depreciation':
            # Calculate totals for the visible queryset (respects filters)
            queryset = self.get_queryset()
            all_visible = list(queryset)
            
            total_cost = sum((a.purchase_price or 0) for a in all_visible)
            total_acc_dep = sum(a.accumulated_depreciation for a in all_visible)
            total_nbv = sum(a.current_value for a in all_visible)
            
            context['total_cost'] = total_cost
            context['total_acc_dep'] = total_acc_dep
            context['total_nbv'] = total_nbv
            context['is_report'] = True
            
        return context

class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('asset-list')

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

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            messages.error(self.request, "File encoding error. Please ensure the CSV is UTF-8 encoded.")
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"Error reading file: {str(e)}")
            return self.form_invalid(form)

        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        errors = []
        assets_to_create = []

        # 1. Validation Phase
        for row_idx, row in enumerate(reader, start=1):
            try:
                # Basic Fields
                name = row.get('name', '').strip()
                asset_tag = row.get('asset_tag', '').strip()
                category_code = row.get('category_code', '').strip()
                
                # Only name and category_code are required, asset_tag will be auto-generated if empty
                if not all([name, category_code]):
                    raise ValueError(f"Missing required fields (name, category_code).")
                
                # Auto-generate asset tag if not provided
                if not asset_tag:
                    asset_tag = generate_asset_tag(self.request.user.organization)

                # Category (Strict)
                try:
                    category = Category.objects.get(
                        organization=self.request.user.organization, 
                        code=category_code
                    )
                except Category.DoesNotExist:
                    raise ValueError(f"Category code '{category_code}' not found.")

                # Status
                status_input = row.get('status', 'ACTIVE').upper()
                status = Asset.Status.ACTIVE
                if status_input in Asset.Status.values:
                    status = status_input
                
                # Location Logic (Strict Chain)
                branch_name = row.get('branch', '').strip()
                building_name = row.get('building', '').strip()
                floor_name = row.get('floor', '').strip()
                room_name = row.get('room', '').strip()
                
                branch = None
                building = None
                floor = None
                room = None

                if branch_name:
                    try:
                        branch = Branch.objects.get(organization=self.request.user.organization, name__iexact=branch_name)
                    except Branch.DoesNotExist:
                        raise ValueError(f"Branch '{branch_name}' not found. (Strict Mode)")

                if building_name:
                    if not branch: raise ValueError(f"Building '{building_name}' designated but no valid Branch provided.")
                    try:
                        building = Building.objects.get(branch=branch, name__iexact=building_name)
                    except Building.DoesNotExist:
                        raise ValueError(f"Building '{building_name}' not found in Branch '{branch.name}'. (Strict Mode)")

                if floor_name:
                    if not building: raise ValueError(f"Floor '{floor_name}' designated but no valid Building provided.")
                    try:
                        floor = Floor.objects.get(building=building, name__iexact=floor_name)
                    except Floor.DoesNotExist:
                        raise ValueError(f"Floor '{floor_name}' not found in Building '{building.name}'. (Strict Mode)")

                if room_name:
                    if not floor: raise ValueError(f"Room '{room_name}' designated but no valid Floor provided.")
                    # Fetch or Create Room manually to handle iexact correctly
                    room = Room.objects.filter(floor=floor, name__iexact=room_name).first()
                    if not room:
                        room = Room.objects.create(floor=floor, name=room_name)

                # Vendor (Strict)
                vendor_name = row.get('vendor', '').strip()
                vendor = None
                if vendor_name:
                    try:
                        vendor = Vendor.objects.get(organization=self.request.user.organization, name__iexact=vendor_name)
                    except Vendor.DoesNotExist:
                        raise ValueError(f"Vendor '{vendor_name}' not found. (Strict Mode)")

                # Gather Data
                assets_to_create.append(Asset(
                    organization=self.request.user.organization,
                    name=name,
                    asset_tag=asset_tag,
                    category=category,
                    status=status,
                    purchase_price=row.get('purchase_price') or None,
                    brand=row.get('brand', '').strip(),
                    model=row.get('model', '').strip(),
                    serial_number=row.get('serial_number', '').strip(),
                    notes=row.get('notes', '').strip(),
                    branch=branch,
                    building=building,
                    floor=floor,
                    room=room,
                    vendor=vendor,
                    useful_life_years=category.useful_life_years,
                    depreciation_method=category.depreciation_method,
                    created_by=self.request.user
                ))

            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")
        
        if errors:
            for err in errors[:10]: # Show first 10 errors
                messages.error(self.request, err)
            if len(errors) > 10:
                messages.error(self.request, f"...and {len(errors) - 10} more errors.")
            messages.warning(self.request, "Import aborted due to validation errors. No assets were created.")
            return self.form_invalid(form)
        
        if not assets_to_create:
            messages.warning(self.request, "No valid assets found in the CSV file.")
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                for asset in assets_to_create:
                    asset.save()
                messages.success(self.request, f"Successfully imported {len(assets_to_create)} assets.")
        except Exception as e:
            messages.error(self.request, f"Database error during save: {str(e)}")
            return self.form_invalid(form)

        return redirect(self.success_url)

class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    template_name = 'assets/asset_detail.html'
    context_object_name = 'asset'

    def get_queryset(self):
        return Asset.objects.filter(organization=self.request.user.organization)
    
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

