from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.assets.models import Asset, Group, SubGroup, Category, SubCategory
from apps.locations.models import Region, Site, Building, Floor
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from django.core.cache import cache

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['last_updated'] = timezone.now()
        
        # Determine if financial data should be shown - for CHECKER and above roles
        user = self.request.user
        from apps.users.models import User
        show_financial = user.role in [User.Role.CHECKER, User.Role.SENIOR_MANAGER, User.Role.ADMIN] or user.is_superuser
        context['show_financial'] = show_financial
        
        # Filter by organization
        if self.request.user.is_authenticated and hasattr(self.request.user, 'organization'):
            org = self.request.user.organization
            
            # Try to get cached dashboard data (cache for 5 minutes)
            cache_key = f'dashboard_data_{org.id}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                context.update(cached_data)
                return context
            
            # Optimize queries - only select needed fields
            qs = Asset.objects.filter(
                organization=org,
                is_deleted=False
            ).select_related(
                'category', 'assigned_to'
            )
            
            # Use database aggregation for counts - much faster
            context['total_assets'] = qs.count()
            
            # Calculate total purchase price from database
            agg = qs.aggregate(
                total_purchase=Coalesce(Sum('purchase_price'), Decimal('0'))
            )
            
            total_purchase = agg['total_purchase']
            context['total_value'] = total_purchase
            
            # OPTIMIZED: Calculate depreciation only for assets with purchase_price
            # Process in smaller batches to avoid memory issues
            assets_with_price = qs.filter(purchase_price__isnull=False)
            
            total_nbv = Decimal('0')
            total_dep = Decimal('0')
            
            # Process in chunks to avoid memory issues
            batch_size = 1000
            for i in range(0, assets_with_price.count(), batch_size):
                batch = list(assets_with_price[i:i+batch_size])
                for asset in batch:
                    total_nbv += asset.current_value
                    total_dep += asset.accumulated_depreciation
            
            context['total_nbv'] = total_nbv
            context['total_depreciation'] = total_dep
            
            # Calculate depreciation percentage
            if total_purchase > 0:
                dep_per = (total_dep / total_purchase) * 100
                context['depreciation_percentage'] = float(dep_per)
                context['remaining_percentage'] = 100 - float(dep_per)
            else:
                context['depreciation_percentage'] = 0
                context['remaining_percentage'] = 100
            
            # Status counts using database aggregation - fast!
            context['assigned_assets'] = qs.filter(assigned_to__isnull=False).count()
            context['in_repair_assets'] = qs.filter(status=Asset.Status.UNDER_MAINTENANCE).count()
            context['in_storage_assets'] = qs.filter(status=Asset.Status.IN_STORAGE).count()
            context['active_assets'] = qs.filter(status=Asset.Status.ACTIVE).count()
            
            # Category breakdown (top 5) - already optimized
            category_data = qs.values('category__name').annotate(count=Count('id')).order_by('-count')[:5]
            context['category_breakdown'] = category_data
            
            # Status distribution with efficient query
            status_data = []
            status_agg = qs.values('status').annotate(count=Count('id')).order_by('-count')
            status_dict = {s[0]: s[1] for s in Asset.Status.choices}
            
            for item in status_agg:
                if item['count'] > 0:
                    status_data.append({
                        'status': status_dict.get(item['status'], item['status']),
                        'count': item['count'],
                        'code': item['status']
                    })
            context['status_distribution'] = status_data
            
            # Group-wise asset count (for new chart) - optimized
            group_data = qs.values('group__name').annotate(count=Count('id')).order_by('-count')[:10]
            group_list = []
            for group in group_data:
                group_list.append({
                    'name': group['group__name'] or 'Ungrouped',
                    'count': group['count']
                })
            # Add ungrouped assets
            ungrouped_count = qs.filter(group__isnull=True).count()
            if ungrouped_count > 0:
                group_list.append({
                    'name': 'Ungrouped',
                    'count': ungrouped_count
                })
            context['group_distribution'] = group_list
            
            # Recent assets - just 5 items, no need to optimize heavily
            context['recent_assets'] = qs.order_by('-created_at')[:5]
            
            # Master Data Counts - already optimized (just counts)
            context['group_count'] = Group.objects.filter(organization=org).count()
            context['sub_group_count'] = SubGroup.objects.filter(organization=org).count()
            context['category_count'] = Category.objects.filter(organization=org).count()
            context['sub_category_count'] = SubCategory.objects.filter(organization=org).count()
            
            context['region_count'] = Region.objects.filter(organization=org).count()
            context['site_count'] = Site.objects.filter(organization=org).count()
            context['building_count'] = Building.objects.filter(organization=org).count()
            context['floor_count'] = Floor.objects.filter(organization=org).count()
            
            # Cache the dashboard data for 5 minutes (300 seconds)
            cache_data = {
                'total_assets': context['total_assets'],
                'total_value': context['total_value'],
                'total_nbv': context['total_nbv'],
                'total_depreciation': context['total_depreciation'],
                'depreciation_percentage': context['depreciation_percentage'],
                'remaining_percentage': context['remaining_percentage'],
                'assigned_assets': context['assigned_assets'],
                'in_repair_assets': context['in_repair_assets'],
                'in_storage_assets': context['in_storage_assets'],
                'active_assets': context['active_assets'],
                'category_breakdown': context['category_breakdown'],
                'status_distribution': context['status_distribution'],
                'group_distribution': context['group_distribution'],
                'recent_assets': context['recent_assets'],
                'group_count': context['group_count'],
                'sub_group_count': context['sub_group_count'],
                'category_count': context['category_count'],
                'sub_category_count': context['sub_category_count'],
                'region_count': context['region_count'],
                'site_count': context['site_count'],
                'building_count': context['building_count'],
                'floor_count': context['floor_count'],
            }
            cache.set(cache_key, cache_data, 300)
            
        else:
            context['total_assets'] = 0
            context['total_value'] = Decimal('0')
            context['total_nbv'] = Decimal('0')
            context['total_depreciation'] = Decimal('0')
            context['depreciation_percentage'] = 0
            context['assigned_assets'] = 0
            context['in_repair_assets'] = 0
            context['in_storage_assets'] = 0
            context['active_assets'] = 0
            context['category_breakdown'] = []
            context['status_distribution'] = []
            
        return context

