# --- DEPRECIATION REPORT VIEWS ---
class DepreciationReportCategoryView(LoginRequiredMixin, ListView):
    """Dedicated view for category-based depreciation report"""
    model = Asset
    template_name = 'assets/depreciation_report_category.html'
    context_object_name = 'assets'
    paginate_by = 50

    def get_queryset(self):
        queryset = Asset.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False
        ).select_related(
            'category', 'sub_category', 'branch', 'assigned_to', 
            'site', 'building', 'brand_new', 'room', 'department',
            'region', 'location', 'sub_location', 'vendor', 
            'supplier', 'company', 'group', 'custodian'
        )

        # Search filter
        query = self.request.GET.get('q')
        if query:
            q = (
                Q(name__icontains=query) |
                Q(asset_tag__icontains=query) |
                Q(custom_asset_tag__icontains=query) |
                Q(asset_code__icontains=query) |
                Q(serial_number__icontains=query) |
                Q(category__name__icontains=query)
            )
            queryset = queryset.filter(q)
        
        # Date range filters
        depr_date_from = self.request.GET.get('depr_date_from')
        depr_date_to = self.request.GET.get('depr_date_to')
        
        if depr_date_from:
            queryset = queryset.filter(purchase_date__gte=depr_date_from)
        if depr_date_to:
            queryset = queryset.filter(purchase_date__lte=depr_date_to)
        
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
        
        return queryset.order_by('-purchase_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        queryset = self.get_queryset()
        
        # Summary totals
        from django.db.models import Sum, Count
        from django.db.models.functions import Coalesce
        
        agg = queryset.aggregate(
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            total_count=Count('id')
        )
        
        total_cost = agg['total_cost']
        total_count = agg['total_count']
        
        SAMPLE_SIZE = 5000
        if total_count > SAMPLE_SIZE:
            sample_qs = queryset[:SAMPLE_SIZE]
            sample_list = list(sample_qs)
            avg_depreciation_ratio = (
                sum(a.accumulated_depreciation for a in sample_list) / 
                sum(a.purchase_price or Decimal('0') for a in sample_list)
            ) if any(a.purchase_price for a in sample_list) else 0
            
            total_acc_dep = total_cost * Decimal(str(avg_depreciation_ratio))
            total_nbv = total_cost - total_acc_dep
            context['is_estimate'] = True
            context['sample_size'] = SAMPLE_SIZE
        else:
            all_visible = list(queryset)
            total_acc_dep = sum(a.accumulated_depreciation for a in all_visible) if all_visible else Decimal('0')
            total_nbv = sum(a.current_value for a in all_visible) if all_visible else Decimal('0')
            context['is_estimate'] = False
        
        context['total_cost'] = total_cost
        context['total_acc_dep'] = total_acc_dep
        context['total_nbv'] = total_nbv
        context['total_assets_report'] = total_count
        
        # Category grouping
        grouped_data = queryset.values('category', 'category__name').annotate(
            count=Count('id'),
            total_cost=Sum('purchase_price')
        ).order_by('-total_cost')[:100]
        
        grouped_list = []
        for group in grouped_data:
            cat_id = group['category']
            cat_qs = queryset.filter(category_id=cat_id)
            cat_count = group['count']
            
            if cat_count > SAMPLE_SIZE:
                sample = list(cat_qs[:SAMPLE_SIZE])
                if sample and any(a.purchase_price for a in sample):
                    avg_dep = sum(a.accumulated_depreciation for a in sample) / sum(a.purchase_price or Decimal('0') for a in sample if a.purchase_price)
                    total_cat_dep = (group['total_cost'] or Decimal('0')) * Decimal(str(avg_dep))
                else:
                    total_cat_dep = Decimal('0')
            else:
                cat_assets = list(cat_qs)
                total_cat_dep = sum(a.accumulated_depreciation for a in cat_assets) if cat_assets else Decimal('0')
            
            grouped_list.append({
                'id': cat_id,
                'name': group['category__name'] or 'Uncategorized',
                'total_cost': group['total_cost'] or Decimal('0'),
                'total_acc_dep': total_cat_dep,
                'total_nbv': (group['total_cost'] or Decimal('0')) - total_cat_dep,
                'count': cat_count,
            })
        
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
        
        return context
