# 🚀 API Development - Getting Started

## ✅ What Has Been Completed

### 1. API Structure Created
- New `apps/api` application with versioning support (v1)
- Clean separation between web and API endpoints
- Ready for future API versions (v2, v3, etc.)

### 2. Authentication System
- **JWT (JSON Web Token)** authentication implemented
- **Session authentication** maintained for backward compatibility
- Token-based security for mobile/external apps

### 3. Available API Endpoints

#### Authentication APIs (Completed ✅)
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/` | GET | API root | No |
| `/api/v1/auth/login/` | POST | User login | No |
| `/api/v1/auth/register/` | POST | User registration | No |
| `/api/v1/auth/logout/` | POST | User logout | Yes |
| `/api/v1/auth/profile/` | GET, PUT | Get/Update profile | Yes |
| `/api/v1/auth/change-password/` | POST | Change password | Yes |
| `/api/v1/auth/token/refresh/` | POST | Refresh token | No |

### 4. Documentation
- **Swagger UI**: Interactive API testing at `/api/docs/`
- **ReDoc**: Beautiful API docs at `/api/redoc/`
- Comprehensive documentation files created

---

## 📦 Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

**New packages added:**
- `djangorestframework-simplejwt` - JWT authentication
- `drf-yasg` - API documentation (Swagger/OpenAPI)

### Step 2: Run Migrations
```bash
python manage.py migrate
```

### Step 3: Create Test User (if needed)
```bash
python manage.py createsuperuser
```

### Step 4: Start Development Server
```bash
python manage.py runserver
```

---

## 🧪 Testing the API

### Option 1: Run Test Script
```bash
python test_api_login.py
```

### Option 2: Use Interactive Documentation
1. Open browser: http://localhost:8000/api/docs/
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters and click "Execute"

### Option 3: Use cURL
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"your_password\"}"

# Get Profile (replace TOKEN with your access token)
curl -X GET http://localhost:8000/api/v1/auth/profile/ \
  -H "Authorization: Bearer TOKEN"
```

### Option 4: Use Postman
1. Import the API endpoints
2. Create a new POST request to: `http://localhost:8000/api/v1/auth/login/`
3. Body (JSON):
```json
{
    "username": "your_username",
    "password": "your_password"
}
```
4. Copy the `access` token from response
5. For authenticated requests, add header:
   - Key: `Authorization`
   - Value: `Bearer YOUR_ACCESS_TOKEN`

---

## 📁 Project Structure

```
apps/
├── api/
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py                    # Main API URL router
│   └── v1/
│       ├── __init__.py
│       ├── serializers.py         # Data serializers
│       ├── views.py              # API views/endpoints
│       └── urls.py               # v1 URL patterns
├── assets/                        # Asset management app
├── users/                         # User management app
├── locations/                     # Location management app
└── ...

Documentation:
├── API_DOCUMENTATION.md          # Detailed API docs
├── API_QUICK_START.md           # Quick reference guide
└── API_README.md                # This file
```

---

## 🔑 Authentication Flow

### 1. Login
```
POST /api/v1/auth/login/
{
    "username": "user",
    "password": "pass"
}

Response:
{
    "user": {...},
    "tokens": {
        "access": "eyJ0eXAi...",  // Use this for API calls
        "refresh": "eyJ0eXAi..."  // Use to get new access token
    }
}
```

### 2. Make Authenticated Requests
```
GET /api/v1/auth/profile/
Headers:
    Authorization: Bearer eyJ0eXAi...
```

### 3. Refresh Token (when access token expires)
```
POST /api/v1/auth/token/refresh/
{
    "refresh": "eyJ0eXAi..."
}

Response:
{
    "access": "new_access_token"
}
```

---

## 🎯 Next Steps for API Development

### Phase 2: Assets API (Recommended Next) 📋
```
GET    /api/v1/assets/              # List all assets
POST   /api/v1/assets/              # Create asset
GET    /api/v1/assets/{id}/         # Get asset details
PUT    /api/v1/assets/{id}/         # Update asset
DELETE /api/v1/assets/{id}/         # Delete asset
GET    /api/v1/assets/search/       # Search assets
```

### Phase 3: Locations API 📋
```
GET    /api/v1/locations/branches/
POST   /api/v1/locations/branches/
GET    /api/v1/locations/departments/
POST   /api/v1/locations/departments/
```

### Phase 4: Reports API 📋
```
GET    /api/v1/reports/assets/
GET    /api/v1/reports/depreciation/
GET    /api/v1/reports/transfers/
```

### Phase 5: Advanced Features 📋
- File uploads (asset images)
- Bulk operations
- Export to Excel/PDF
- Real-time notifications
- WebSocket support

---

## 🔒 Security Configuration

### Current Settings (settings.py)

**JWT Token Lifetime:**
- Access Token: 1 hour
- Refresh Token: 7 days

**Authentication Methods:**
1. JWT (Primary for API)
2. Session (For web interface)
3. Basic Auth (For testing)

**CORS (Add when needed):**
```python
# Install: pip install django-cors-headers
INSTALLED_APPS += ['corsheaders']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', ...]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React app
    "http://localhost:8080",  # Vue app
]
```

---

## 📚 Documentation Links

- **Detailed API Docs**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Quick Start**: [API_QUICK_START.md](API_QUICK_START.md)
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

---

## 🐛 Troubleshooting

### Issue: "Invalid token" error
**Solution:** Token might have expired. Use refresh token to get a new access token.

### Issue: "Authentication credentials were not provided"
**Solution:** Make sure to include the Authorization header:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Issue: CORS errors in browser
**Solution:** Install and configure django-cors-headers (see Security Configuration above)

### Issue: "Method not allowed"
**Solution:** Check if you're using the correct HTTP method (GET, POST, PUT, DELETE)

---

## 🤝 Contributing to API Development

### Adding a New Endpoint

1. **Create Serializer** (`apps/api/v1/serializers.py`):
```python
class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'
```

2. **Create View** (`apps/api/v1/views.py`):
```python
class MyModelAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Your logic here
        return Response(data)
```

3. **Add URL** (`apps/api/v1/urls.py`):
```python
path('mymodel/', views.MyModelAPIView.as_view(), name='mymodel'),
```

---

## 📞 Support

For questions or issues:
1. Check documentation files
2. Visit Swagger UI for interactive testing
3. Review the test script examples
4. Contact the development team

---

**Version**: 1.0  
**Last Updated**: March 3, 2026  
**Status**: Phase 1 Complete ✅
