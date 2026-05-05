class AssetReconciliationReportView(LoginRequiredMixin, View):
    """Comprehensive Asset Reconciliation Report GÇö full-picture summary of the asset register."""
    template_name = 'assets/reconciliation_report.html'

    def get(self, request):
        from django.db.models import Sum, Count, Q
        from django.db.models.functions import Coalesce

        org = request.user.organization
        date_from_str = request.GET.get('date_from', '')
        date_to_str = request.GET.get('date_to', '')

        date_from = None
        date_to = None
        try:
            if date_from_str:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
        try:
            if date_to_str:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass

        base_qs = Asset.objects.filter(organization=org, is_deleted=False)

        # --- Period slicing ---
        if date_from:
            period_qs = base_qs.filter(purchase_date__gte=date_from)
        else:
            period_qs = base_qs

        if date_to:
            period_qs = period_qs.filter(purchase_date__lte=date_to)

        # Additions in period (purchased within range)
        additions_qs = period_qs if (date_from or date_to) else base_qs.none()

        # Opening balance: purchased before date_from
        if date_from:
            opening_qs = base_qs.filter(Q(purchase_date__lt=date_from) | Q(purchase_date__isnull=True))
        else:
            opening_qs = base_qs.none()

        # --- Helper: aggregate financials from a queryset ---
        def agg_financials(qs):
            result = qs.aggregate(
                count=Count('id'),
                total_cost=Coalesce(Sum('purchase_price'), Decimal('0')),
            )
            assets_list = list(qs)
            acc_dep = sum(a.accumulated_depreciation for a in assets_list)
            nbv = sum(a.current_value for a in assets_list)
            result['acc_dep'] = acc_dep
            result['nbv'] = nbv
            return result

        # Overall totals (all assets, no date filter)
        all_assets = list(base_qs.select_related('category', 'department', 'site'))
        total_count = len(all_assets)
        total_cost = sum((a.purchase_price or Decimal('0')) for a in all_assets)
        total_acc_dep = sum(a.accumulated_depreciation for a in all_assets)
        total_nbv = sum(a.current_value for a in all_assets)

        # Opening / additions / closing
        opening_data = agg_financials(opening_qs) if date_from else None
        additions_data = agg_financials(additions_qs) if (date_from or date_to) else None
        closing_data = agg_financials(base_qs.filter(purchase_date__lte=date_to) if date_to else base_qs)

        # --- By Category ---
        by_category = []
        cat_groups = base_qs.values('category__id', 'category__name').annotate(
            count=Count('id'),
            total_cost=Coalesce(Sum('purchase_price'), Decimal('0'))
        ).order_by('-total_cost')
        for row in cat_groups:
            cat_assets = [a for a in all_assets if a.category_id == row['category__id']]
            acc = sum(a.accumulated_depreciation for a in cat_assets)
            nbv = sum(a.current_value for a in cat_assets)
            by_category.append({
                'name': row['category__name'] or 'Uncategorized',
                'count': row['count'],
                'cost': row['total_cost'] or Decimal('0'),
                'acc_dep': acc,
                'nbv': nbv,
            })

        # --- By Status ---
        by_status = []
        for code, label in Asset.Status.choices:
            status_assets = [a for a in all_assets if a.status == code]
            cost = sum((a.purchase_price or Decimal('0')) for a in status_assets)
            acc = sum(a.accumulated_depreciation for a in status_assets)
            nbv = sum(a.current_value for a in status_assets)
            by_status.append({
                'label': label, 'count': len(status_assets),
                'cost': cost, 'acc_dep': acc, 'nbv': nbv,
            })

        # --- By Condition ---
        by_condition = []
        for code, label in Asset.Condition.choices:
            c_assets = [a for a in all_assets if a.condition == code]
            cost = sum((a.purchase_price or Decimal('0')) for a in c_assets)
            acc = sum(a.accumulated_depreciation for a in c_assets)
            nbv = sum(a.current_value for a in c_assets)
            by_condition.append({
                'label': label, 'count': len(c_assets),
                'cost': cost, 'acc_dep': acc, 'nbv': nbv,
            })

        # --- Tagged vs Untagged ---
        tagged_assets = [a for a in all_assets if a.is_tagged]
        untagged_assets = [a for a in all_assets if not a.is_tagged]
        by_tagged = [
            {
                'label': 'Tagged',
                'count': len(tagged_assets),
                'cost': sum((a.purchase_price or Decimal('0')) for a in tagged_assets),
                'acc_dep': sum(a.accumulated_depreciation for a in tagged_assets),
                'nbv': sum(a.current_value for a in tagged_assets),
            },
            {
                'label': 'Untagged',
                'count': len(untagged_assets),
                'cost': sum((a.purchase_price or Decimal('0')) for a in untagged_assets),
                'acc_dep': sum(a.accumulated_depreciation for a in untagged_assets),
                'nbv': sum(a.current_value for a in untagged_assets),
            },
        ]

        # --- By Department ---
        by_department = []
        dept_map = {}
        for a in all_assets:
            key = a.department_id
            label = a.department.name if a.department else 'No Department'
            if key not in dept_map:
                dept_map[key] = {'label': label, 'assets': []}
            dept_map[key]['assets'].append(a)
        for entry in sorted(dept_map.values(), key=lambda x: -sum((a.purchase_price or 0) for a in x['assets'])):
            a_list = entry['assets']
            by_department.append({
                'label': entry['label'],
                'count': len(a_list),
                'cost': sum((a.purchase_price or Decimal('0')) for a in a_list),
                'acc_dep': sum(a.accumulated_depreciation for a in a_list),
                'nbv': sum(a.current_value for a in a_list),
            })

        # --- By Site ---
        by_site = []
        site_map = {}
        for a in all_assets:
            key = a.site_id
            label = a.site.name if a.site else 'No Site'
            if key not in site_map:
                site_map[key] = {'label': label, 'assets': []}
            site_map[key]['assets'].append(a)
        for entry in sorted(site_map.values(), key=lambda x: -sum((a.purchase_price or 0) for a in x['assets'])):
            a_list = entry['assets']
            by_site.append({
                'label': entry['label'],
                'count': len(a_list),
                'cost': sum((a.purchase_price or Decimal('0')) for a in a_list),
                'acc_dep': sum(a.accumulated_depreciation for a in a_list),
                'nbv': sum(a.current_value for a in a_list),
            })

        context = {
            # Totals
            'total_count': total_count,
            'total_cost': total_cost,
            'total_acc_dep': total_acc_dep,
            'total_nbv': total_nbv,
            # Period
            'date_from': date_from_str,
            'date_to': date_to_str,
            'opening_data': opening_data,
            'additions_data': additions_data,
            'closing_data': closing_data,
            # Breakdowns
            'by_category': by_category,
            'by_status': by_status,
            'by_condition': by_condition,
            'by_tagged': by_tagged,
            'by_department': by_department,
            'by_site': by_site,
            # Currency
            'currency': 'AED',
        }
        return render(request, self.template_name, context)


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

