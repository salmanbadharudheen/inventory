from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    LoginSerializer, 
    UserSerializer, 
    RegisterSerializer,
    ChangePasswordSerializer,
    AssetCreateSerializer,
    AssetReadSerializer,
    AssetListSerializer,
    CategoryLookupSerializer,
    SubCategoryLookupSerializer,
    GroupLookupSerializer,
    SubGroupLookupSerializer,
    CompanyLookupSerializer,
    RegionLookupSerializer,
    SiteLookupSerializer,
    BuildingLookupSerializer,
    FloorLookupSerializer,
    BranchLookupSerializer,
    DepartmentLookupSerializer,
)


class LoginAPIView(APIView):
    """
    API endpoint for user login.
    
    POST /api/v1/auth/login/
    Request Body:
    {
        "username": "your_username",
        "password": "your_password"
    }
    
    Response:
    {
        "user": {...},
        "tokens": {
            "access": "...",
            "refresh": "..."
        },
        "message": "Login successful"
    }
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Login user",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Validation error",
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Login user (for session-based as well)
            login(request, user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    API endpoint for user logout.
    
    POST /api/v1/auth/logout/
    Headers: Authorization: Bearer <access_token>
    
    Response:
    {
        "message": "Logout successful"
    }
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Logout user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response(
                description="Logout successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'message': openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            400: "Logout failed",
        },
    )
    def post(self, request):
        try:
            # Logout from session
            logout(request)
            
            # Optionally blacklist the refresh token if using token blacklist
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    """
    API endpoint for user registration.
    
    POST /api/v1/auth/register/
    Request Body:
    {
        "username": "new_user",
        "email": "user@example.com",
        "password": "secure_password",
        "password2": "secure_password",
        "first_name": "John",
        "last_name": "Doe",
        "role": "EMPLOYEE"
    }
    
    Response:
    {
        "user": {...},
        "tokens": {
            "access": "...",
            "refresh": "..."
        },
        "message": "Registration successful"
    }
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Register user",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="Registration successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Validation error",
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """
    API endpoint to get current user profile.
    
    GET /api/v1/auth/profile/
    Headers: Authorization: Bearer <access_token>
    
    Response:
    {
        "user": {...}
    }
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get current user profile",
        responses={200: UserSerializer},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Update current user profile",
        request_body=UserSerializer,
        responses={200: UserSerializer, 400: "Validation error"},
    )
    def put(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'user': serializer.data,
                'message': 'Profile updated successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordAPIView(APIView):
    """
    API endpoint to change user password.
    
    POST /api/v1/auth/change-password/
    Headers: Authorization: Bearer <access_token>
    Request Body:
    {
        "old_password": "current_password",
        "new_password": "new_password",
        "new_password2": "new_password"
    }
    
    Response:
    {
        "message": "Password changed successfully"
    }
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Change user password",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'message': openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            400: "Validation error",
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
@swagger_auto_schema(
    operation_summary='API root',
    responses={
        200: openapi.Response(
            description='API root endpoints',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT),
        )
    },
)
def api_root(request):
    """
    API Root endpoint - provides an overview of available API endpoints.
    
    GET /api/v1/
    """
    return Response({
        'message': 'Welcome to Inventory Management API',
        'version': 'v1',
        'endpoints': {
            'auth': {
                'login': '/api/v1/auth/login/',
                'logout': '/api/v1/auth/logout/',
                'register': '/api/v1/auth/register/',
                'profile': '/api/v1/auth/profile/',
                'change_password': '/api/v1/auth/change-password/',
                'token_refresh': '/api/v1/auth/token/refresh/',
            },
            'documentation': {
                'swagger': '/api/docs/',
                'redoc': '/api/redoc/',
            }
        }
    })


class DashboardAPIView(APIView):
    """
    API endpoint for mobile dashboard stats.

    GET /api/v1/dashboard/
    Headers: Authorization: Bearer <access_token>

    Optimised for 400K+ assets: all counts and financial totals are computed
    in a **single SQL query** using conditional aggregation.  Depreciation is
    estimated via pure SQL (straight-line approximation) – no Python loops.
    """
    permission_classes = [IsAuthenticated]

    EMPTY_DASHBOARD = {
        'total_assets': 0,
        'active_assets': 0,
        'assigned_assets': 0,
        'in_repair_assets': 0,
        'in_storage_assets': 0,
        'show_financial': False,
        'total_value': '0.00',
        'total_nbv': '0.00',
        'total_depreciation': '0.00',
        'depreciation_percentage': 0,
        'category_breakdown': [],
        'status_distribution': [],
        'recent_assets': [],
        'master_data': {
            'groups': 0, 'sub_groups': 0,
            'categories': 0, 'sub_categories': 0,
            'regions': 0, 'sites': 0,
            'buildings': 0, 'floors': 0,
        },
    }

    def get(self, request):
        from apps.assets.models import Asset, Group, SubGroup, Category, SubCategory
        from apps.locations.models import Region, Site, Building, Floor
        from apps.users.models import User
        from django.db.models import F, Value, DecimalField, IntegerField
        from django.db.models.functions import Coalesce as CoalesceFunc, Greatest

        user = request.user
        show_financial = user.role in [
            User.Role.CHECKER, User.Role.SENIOR_MANAGER, User.Role.ADMIN
        ] or user.is_superuser

        if not (user.is_authenticated and hasattr(user, 'organization') and user.organization):
            empty = dict(self.EMPTY_DASHBOARD)
            empty['show_financial'] = show_financial
            return Response(empty)

        org = user.organization
        cache_key = f'api_dashboard_{org.id}'
        cached = cache.get(cache_key)
        if cached:
            cached['show_financial'] = show_financial
            return Response(cached)

        qs = Asset.objects.filter(organization=org, is_deleted=False)

        # ── 1) Single query: all counts + financial totals ────────────
        from django.db.models import Q
        today = timezone.now().date()

        agg = qs.aggregate(
            total_assets=Count('id'),
            active_assets=Count('id', filter=Q(status=Asset.Status.ACTIVE)),
            assigned_assets=Count('id', filter=Q(assigned_to__isnull=False)),
            in_repair_assets=Count('id', filter=Q(status=Asset.Status.UNDER_MAINTENANCE)),
            in_storage_assets=Count('id', filter=Q(status=Asset.Status.IN_STORAGE)),
            total_purchase=Coalesce(Sum('purchase_price'), Decimal('0')),
        )

        total_assets = agg['total_assets']
        total_purchase = agg['total_purchase']

        # ── 2) Depreciation via SQL (straight-line approximation) ─────
        # years_passed = (today - purchase_date).days / 365.25
        # annual_dep   = (purchase_price - salvage_value) / useful_life_years
        # acc_dep      = min(annual_dep * years_passed, purchase_price - salvage_value)
        # We compute SUM(acc_dep) and SUM(nbv) entirely in SQL.
        from django.db.models import ExpressionWrapper, Case, When
        from django.db.models.functions import Cast

        dep_qs = qs.filter(
            purchase_price__isnull=False,
            purchase_date__isnull=False,
            useful_life_years__isnull=False,
            useful_life_years__gt=0,
        )

        # PostgreSQL: (CURRENT_DATE - date_column) returns integer days
        from django.db.models import Func

        class DaysSince(Func):
            """Return integer days between purchase_date and today (PostgreSQL)."""
            function = ''
            template = "(CURRENT_DATE - %(expressions)s)"
            output_field = IntegerField()

        dep_agg = dep_qs.annotate(
            _days_passed=DaysSince(F('purchase_date')),
        ).annotate(
            _years_passed=ExpressionWrapper(
                F('_days_passed') * Value(1.0) / Value(365.25),
                output_field=DecimalField(max_digits=10, decimal_places=4),
            ),
            _depreciable=ExpressionWrapper(
                F('purchase_price') - CoalesceFunc(F('salvage_value'), Value(0)),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
            _annual_dep=ExpressionWrapper(
                (F('purchase_price') - CoalesceFunc(F('salvage_value'), Value(0)))
                * Value(1.0)
                / F('useful_life_years'),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
        ).annotate(
            _raw_dep=ExpressionWrapper(
                F('_annual_dep') * F('_years_passed'),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
        ).annotate(
            _capped_dep=Case(
                When(_raw_dep__lt=Value(0), then=Value(0)),
                When(_raw_dep__gt=F('_depreciable'), then=F('_depreciable')),
                default=F('_raw_dep'),
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
        ).aggregate(
            total_dep=Coalesce(Sum('_capped_dep'), Decimal('0')),
        )

        total_dep = dep_agg['total_dep']
        if isinstance(total_dep, float):
            total_dep = Decimal(str(total_dep)).quantize(Decimal('0.01'))
        total_nbv = (total_purchase - total_dep)
        if total_nbv < 0:
            total_nbv = Decimal('0')
        dep_pct = float((total_dep / total_purchase) * 100) if total_purchase > 0 else 0

        # ── 3) Category breakdown top 5 (single query) ───────────────
        cat_data = list(
            qs.values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        category_breakdown = [
            {'name': c['category__name'] or 'Uncategorized', 'count': c['count']}
            for c in cat_data
        ]

        # ── 4) Status distribution (single query) ────────────────────
        status_dict = {s[0]: s[1] for s in Asset.Status.choices}
        status_agg = qs.values('status').annotate(count=Count('id')).order_by('-count')
        status_distribution = [
            {'status': status_dict.get(s['status'], s['status']), 'code': s['status'], 'count': s['count']}
            for s in status_agg if s['count'] > 0
        ]

        # ── 5) Recent 5 assets (uses created_at index) ───────────────
        recent = qs.only(
            'id', 'name', 'asset_tag', 'status', 'category',
        ).select_related('category').order_by('-created_at')[:5]
        recent_assets = [
            {
                'id': str(a.id),
                'name': a.name,
                'asset_id': a.asset_tag,
                'status': a.status,
                'category': a.category.name if a.category else '',
            }
            for a in recent
        ]

        # ── 6) Master data counts (single query per model is fine,
        #        these tables are small) ───────────────────────────────
        master = {
            'groups': Group.objects.filter(organization=org).count(),
            'sub_groups': SubGroup.objects.filter(organization=org).count(),
            'categories': Category.objects.filter(organization=org).count(),
            'sub_categories': SubCategory.objects.filter(organization=org).count(),
            'regions': Region.objects.filter(organization=org).count(),
            'sites': Site.objects.filter(organization=org).count(),
            'buildings': Building.objects.filter(organization=org).count(),
            'floors': Floor.objects.filter(organization=org).count(),
        }

        data = {
            'total_assets': total_assets,
            'active_assets': agg['active_assets'],
            'assigned_assets': agg['assigned_assets'],
            'in_repair_assets': agg['in_repair_assets'],
            'in_storage_assets': agg['in_storage_assets'],
            'show_financial': show_financial,
            'total_value': str(total_purchase),
            'total_nbv': str(total_nbv.quantize(Decimal('0.01'))),
            'total_depreciation': str(total_dep.quantize(Decimal('0.01'))),
            'depreciation_percentage': round(dep_pct, 1),
            'category_breakdown': category_breakdown,
            'status_distribution': status_distribution,
            'recent_assets': recent_assets,
            'master_data': master,
        }

        cache.set(cache_key, data, 300)
        data['show_financial'] = show_financial
        return Response(data)


# ────────────────────────────────────────────────────
# Asset CRUD
# ────────────────────────────────────────────────────

class AssetCreateAPIView(APIView):
    """
    POST /api/v1/assets/   – create one (or bulk) asset(s).

    Employee role users go through the approval workflow.
    Other roles create assets directly.
    Quantity > 1 creates multiple assets, each with its own auto-generated tag.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.assets.models import Asset, generate_asset_tag, ApprovalRequest
        from apps.users.models import User

        serializer = AssetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        org = getattr(user, 'organization', None)
        if not org:
            return Response(
                {'detail': 'User has no organization assigned.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Employee approval workflow ────────────────────
        if getattr(user, 'role', None) == User.Role.EMPLOYEE:
            approval_data = {}
            for field_name, value in data.items():
                if value is None:
                    continue
                if hasattr(value, 'pk'):
                    approval_data[field_name] = value.pk
                elif hasattr(value, 'isoformat'):
                    approval_data[field_name] = value.isoformat()
                else:
                    approval_data[field_name] = value
            # Remove file fields from approval JSON
            approval_data.pop('image', None)

            ApprovalRequest.objects.create(
                organization=org,
                requester=user,
                request_type=ApprovalRequest.RequestType.ASSET_CREATE,
                status=ApprovalRequest.Status.PENDING,
                data=approval_data,
                comments='Asset uploaded by employee via mobile and waiting for checker approval.',
            )
            return Response(
                {'detail': 'Asset submitted for approval. It will be added to inventory after checker approval.'},
                status=status.HTTP_202_ACCEPTED,
            )

        # ── Direct creation (Checker / Senior Manager / Admin) ─
        quantity = data.pop('quantity', 1) or 1
        image = data.pop('image', None)

        created_assets = []
        for _ in range(quantity):
            asset = Asset(**data)
            asset.organization = org
            asset.created_by = user
            # asset_tag auto-generated in model save()
            if image:
                asset.image = image
            asset.save()
            created_assets.append(asset)

        # Invalidate dashboard cache
        cache.delete(f'api_dashboard_{org.id}')
        cache.delete(f'dashboard_data_{org.id}')

        if len(created_assets) == 1:
            out = AssetReadSerializer(created_assets[0]).data
        else:
            out = AssetReadSerializer(created_assets, many=True).data

        return Response(
            {'detail': f'{len(created_assets)} asset(s) created.', 'assets': out},
            status=status.HTTP_201_CREATED,
        )


class AssetLookupByTagAPIView(APIView):
    """
    GET /api/v1/assets/lookup/?asset_tag=XXX
    Look up a single asset by its asset_tag (from QR/barcode scan).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.assets.models import Asset
        from django.db.models import Q

        tag = request.query_params.get('asset_tag', '').strip()
        if not tag:
            return Response(
                {'detail': 'asset_tag query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        org = getattr(request.user, 'organization', None)
        if not org:
            return Response(
                {'detail': 'Asset not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        asset = Asset.objects.filter(
            organization=org,
            is_deleted=False,
        ).filter(
            Q(asset_tag__iexact=tag) | Q(custom_asset_tag__iexact=tag)
        ).select_related(
            'category', 'sub_category', 'group', 'sub_group',
            'company', 'department', 'site', 'building',
            'floor', 'region', 'assigned_to', 'branch',
        ).first()

        if not asset:
            return Response(
                {'detail': 'Asset not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(AssetReadSerializer(asset).data)


class AssetDetailAPIView(APIView):
    """
    GET /api/v1/assets/<uuid:pk>/  – retrieve a single asset by UUID.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from apps.assets.models import Asset

        org = getattr(request.user, 'organization', None)
        if not org:
            return Response(
                {'detail': 'Asset not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            asset = Asset.objects.filter(
                organization=org, is_deleted=False
            ).select_related(
                'category', 'sub_category', 'group', 'sub_group',
                'company', 'department', 'site', 'building',
                'floor', 'region', 'assigned_to', 'branch',
            ).get(pk=pk)
        except Asset.DoesNotExist:
            return Response(
                {'detail': 'Asset not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(AssetReadSerializer(asset).data)


class AssetListAPIView(APIView):
    """
    GET /api/v1/assets/   – list assets for the user's organisation.
    Supports ?status=&category=&search= query params.

    Optimised: uses lightweight serializer (no depreciation), only() for fewer
    columns, and proper indexing.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.assets.models import Asset

        org = getattr(request.user, 'organization', None)
        if not org:
            return Response({'count': 0, 'page': 1, 'page_size': 25, 'results': []})

        qs = Asset.objects.filter(organization=org, is_deleted=False).select_related(
            'category', 'company', 'department', 'site', 'building', 'assigned_to',
        ).only(
            'id', 'name', 'asset_tag', 'custom_asset_tag', 'serial_number',
            'status', 'condition', 'asset_type',
            'purchase_date', 'purchase_price', 'currency', 'created_at',
            'category__id', 'category__name',
            'company__id', 'company__name',
            'department__id', 'department__name',
            'site__id', 'site__name',
            'building__id', 'building__name',
            'assigned_to__id', 'assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__username',
        ).order_by('-created_at')

        # filters
        s = request.query_params.get('status')
        if s:
            qs = qs.filter(status=s)
        cat = request.query_params.get('category')
        if cat:
            qs = qs.filter(category_id=cat)
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(asset_tag__icontains=search) |
                Q(serial_number__icontains=search)
            )

        # simple pagination
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 25)), 100)
        total = qs.count()
        start = (page - 1) * page_size
        assets = qs[start:start + page_size]

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': AssetListSerializer(assets, many=True).data,
        })


# ────────────────────────────────────────────────────
# Lookup endpoints (populate dropdowns on mobile)
# ────────────────────────────────────────────────────

class _OrgFilteredListView(APIView):
    """Base for simple org-filtered lookup lists."""
    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None

    def get(self, request):
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        qs = self.model.objects.filter(organization=org).order_by('name')
        # Optional parent filter
        parent_param = getattr(self, 'parent_param', None)
        parent_field = getattr(self, 'parent_field', None)
        if parent_param and parent_field:
            val = request.query_params.get(parent_param)
            if val:
                qs = qs.filter(**{parent_field: val})
        return Response(self.serializer_class(qs, many=True).data)


class CategoryListAPIView(_OrgFilteredListView):
    model = None  # set below
    serializer_class = CategoryLookupSerializer

    def get(self, request):
        from apps.assets.models import Category
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        qs = Category.objects.filter(organization=org).order_by('name')
        return Response(CategoryLookupSerializer(qs, many=True).data)


class SubCategoryListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.assets.models import SubCategory
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        qs = SubCategory.objects.filter(organization=org).order_by('name')
        cat = request.query_params.get('category')
        if cat:
            qs = qs.filter(category_id=cat)
        return Response(SubCategoryLookupSerializer(qs, many=True).data)


class GroupListAPIView(_OrgFilteredListView):
    serializer_class = GroupLookupSerializer

    def get(self, request):
        from apps.assets.models import Group
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        return Response(GroupLookupSerializer(Group.objects.filter(organization=org).order_by('name'), many=True).data)


class SubGroupListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.assets.models import SubGroup
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        qs = SubGroup.objects.filter(organization=org).order_by('name')
        g = request.query_params.get('group')
        if g:
            qs = qs.filter(group_id=g)
        return Response(SubGroupLookupSerializer(qs, many=True).data)


class CompanyListAPIView(_OrgFilteredListView):
    serializer_class = CompanyLookupSerializer

    def get(self, request):
        from apps.assets.models import Company
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        return Response(CompanyLookupSerializer(Company.objects.filter(organization=org).order_by('name'), many=True).data)


class RegionListAPIView(_OrgFilteredListView):
    serializer_class = RegionLookupSerializer

    def get(self, request):
        from apps.locations.models import Region
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        return Response(RegionLookupSerializer(Region.objects.filter(organization=org).order_by('name'), many=True).data)


class SiteListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.locations.models import Site
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        qs = Site.objects.filter(organization=org).order_by('name')
        r = request.query_params.get('region')
        if r:
            qs = qs.filter(region_id=r)
        return Response(SiteLookupSerializer(qs, many=True).data)


class BuildingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.locations.models import Building
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        qs = Building.objects.filter(organization=org).order_by('name')
        s = request.query_params.get('site')
        if s:
            qs = qs.filter(site_id=s)
        return Response(BuildingLookupSerializer(qs, many=True).data)


class FloorListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.locations.models import Floor
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        qs = Floor.objects.filter(organization=org).order_by('name')
        b = request.query_params.get('building')
        if b:
            qs = qs.filter(building_id=b)
        return Response(FloorLookupSerializer(qs, many=True).data)


class BranchListAPIView(_OrgFilteredListView):
    serializer_class = BranchLookupSerializer

    def get(self, request):
        from apps.locations.models import Branch
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        return Response(BranchLookupSerializer(Branch.objects.filter(organization=org).order_by('name'), many=True).data)


class DepartmentListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.locations.models import Department
        org = getattr(request.user, 'organization', None)
        if not org:
            return Response([])
        qs = Department.objects.filter(organization=org).order_by('name')
        b = request.query_params.get('branch')
        if b:
            qs = qs.filter(branch_id=b)
        return Response(DepartmentLookupSerializer(qs, many=True).data)
