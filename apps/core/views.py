from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.assets.models import Asset
from django.db.models import Sum, Count
from django.utils import timezone

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['last_updated'] = timezone.now()
        
        # Filter by organization
        if self.request.user.is_authenticated and hasattr(self.request.user, 'organization'):
            org = self.request.user.organization
            qs = Asset.objects.filter(organization=org)
            
            context['total_assets'] = qs.count()
            
            # Since current_value is a property, we calculate in Python
            all_assets = list(qs)
            total_purchase = sum((a.purchase_price or 0) for a in all_assets)
            total_nbv = sum(a.current_value for a in all_assets)
            total_dep = sum(a.accumulated_depreciation for a in all_assets)
            
            context['total_value'] = total_purchase
            context['total_nbv'] = total_nbv
            context['total_depreciation'] = total_dep
            
            # Calculate depreciation percentage
            if total_purchase > 0:
                context['depreciation_percentage'] = (total_dep / total_purchase) * 100
            else:
                context['depreciation_percentage'] = 0
            
            context['assigned_assets'] = qs.filter(assigned_to__isnull=False).count()
            context['in_repair_assets'] = qs.filter(status=Asset.Status.UNDER_MAINTENANCE).count()
            context['in_storage_assets'] = qs.filter(status=Asset.Status.IN_STORAGE).count()
            context['active_assets'] = qs.filter(status=Asset.Status.ACTIVE).count()
            
            # Category breakdown (top 5)
            category_data = qs.values('category__name').annotate(count=Count('id')).order_by('-count')[:5]
            context['category_breakdown'] = category_data
            
            # Status distribution
            status_data = []
            for status_choice in Asset.Status.choices:
                count = qs.filter(status=status_choice[0]).count()
                if count > 0:
                    status_data.append({
                        'status': status_choice[1],
                        'count': count,
                        'code': status_choice[0]
                    })
            context['status_distribution'] = status_data
            context['recent_assets'] = qs.order_by('-created_at')[:5]
            
        else:
            context['total_assets'] = 0
            context['total_value'] = 0
            context['total_nbv'] = 0
            context['total_depreciation'] = 0
            context['depreciation_percentage'] = 0
            context['assigned_assets'] = 0
            context['in_repair_assets'] = 0
            context['in_storage_assets'] = 0
            context['active_assets'] = 0
            context['category_breakdown'] = []
            context['status_distribution'] = []
            
        return context
