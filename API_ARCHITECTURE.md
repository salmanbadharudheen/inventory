# 📊 API Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATIONS                       │
│  (Mobile App, Web App, Third-party Services, Postman)       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP/HTTPS Requests
                      │ (JSON Format)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Django URLs)                 │
│                    /api/                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│   /api/v1/   │ │/api/docs/│ │ /api/redoc/  │
│   API v1     │ │ Swagger  │ │   ReDoc      │
└──────┬───────┘ └──────────┘ └──────────────┘
       │
       │ Routes to specific endpoints
       │
       ├─────────────────────────────────────────────┐
       │                                             │
       ▼                                             ▼
┌────────────────────────┐              ┌──────────────────────┐
│  Authentication APIs   │              │   Future APIs        │
│  /api/v1/auth/        │              │   (Coming Soon)      │
│                        │              │                      │
│  • login/             │              │  • /api/v1/assets/   │
│  • register/          │              │  • /api/v1/locations/│
│  • logout/            │              │  • /api/v1/reports/  │
│  • profile/           │              │                      │
│  • change-password/   │              └──────────────────────┘
│  • token/refresh/     │
└───────────┬────────────┘
            │
            ▼

┌──────────────────────────────────────────────────────────────┐
│                    MIDDLEWARE LAYER                          │
│  ┌────────────┐ ┌──────────────┐ ┌──────────────────┐      │
│  │   JWT      │ │   Session    │ │   Permission     │      │
│  │   Auth     │ │   Auth       │ │   Checks         │      │
│  └────────────┘ └──────────────┘ └──────────────────┘      │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    API VIEWS (Business Logic)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  LoginAPIView                                        │   │
│  │  RegisterAPIView                                     │   │
│  │  LogoutAPIView                                       │   │
│  │  UserProfileAPIView                                  │   │
│  │  ChangePasswordAPIView                               │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    SERIALIZERS (Data Validation)             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  LoginSerializer                                     │   │
│  │  RegisterSerializer                                  │   │
│  │  UserSerializer                                      │   │
│  │  ChangePasswordSerializer                            │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    MODELS (Database Layer)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  User Model (apps/users/models.py)                   │   │
│  │    - username, email, password                       │   │
│  │    - role, organization, branch                      │   │
│  │    - designation, employee_id                        │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    DATABASE (SQLite/PostgreSQL)              │
│                    Stores all data                           │
└──────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow Diagram

```
┌──────────┐                                        ┌──────────┐
│  Client  │                                        │  Server  │
└────┬─────┘                                        └────┬─────┘
     │                                                   │
     │  POST /api/v1/auth/login/                        │
     │  { username, password }                          │
     ├──────────────────────────────────────────────────►
     │                                                   │
     │                         ┌─────────────────────────┤
     │                         │ Validate credentials    │
     │                         │ Generate JWT tokens     │
     │                         └─────────────────────────┤
     │                                                   │
     │  Response: { user, tokens }                      │
     │◄──────────────────────────────────────────────────┤
     │  { access, refresh }                             │
     │                                                   │
     │                                                   │
     │  GET /api/v1/auth/profile/                       │
     │  Header: Authorization: Bearer <access_token>    │
     ├──────────────────────────────────────────────────►
     │                                                   │
     │                         ┌─────────────────────────┤
     │                         │ Verify JWT token        │
     │                         │ Check permissions       │
     │                         │ Fetch user data         │
     │                         └─────────────────────────┤
     │                                                   │
     │  Response: { user: {...} }                       │
     │◄──────────────────────────────────────────────────┤
     │                                                   │
     │                                                   │
     │  [After 1 hour - token expires]                  │
     │                                                   │
     │  POST /api/v1/auth/token/refresh/                │
     │  { refresh: <refresh_token> }                    │
     ├──────────────────────────────────────────────────►
     │                                                   │
     │                         ┌─────────────────────────┤
     │                         │ Verify refresh token    │
     │                         │ Generate new access     │
     │                         └─────────────────────────┤
     │                                                   │
     │  Response: { access: <new_token> }               │
     │◄──────────────────────────────────────────────────┤
     │                                                   │
```

---

## File Structure

```
inventory/
│
├── apps/
│   ├── api/                          ← NEW API APP
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── urls.py                   ← Main API router
│   │   │
│   │   └── v1/                       ← Version 1 APIs
│   │       ├── __init__.py
│   │       ├── serializers.py        ← Data validation
│   │       ├── views.py              ← Business logic
│   │       └── urls.py               ← Endpoint routes
│   │
│   ├── users/                        ← Existing User app
│   │   └── models.py                 ← User model
│   │
│   ├── assets/                       ← Future: Asset APIs
│   ├── locations/                    ← Future: Location APIs
│   └── ...
│
├── config/
│   ├── settings.py                   ← Updated with DRF config
│   └── urls.py                       ← Added /api/ route
│
├── requirements.txt                  ← Updated packages
│
└── Documentation/
    ├── API_README.md                 ← Main guide
    ├── API_DOCUMENTATION.md          ← Detailed docs
    ├── API_QUICK_START.md            ← Quick reference
    ├── API_SUMMARY.md                ← This summary
    ├── postman_collection.json       ← Postman import
    └── test_api_login.py             ← Test script
```

---

## Request/Response Flow

```
1. Client Makes Request
   ↓
2. Django Receives at /api/v1/auth/login/
   ↓
3. URL Router (config/urls.py → apps/api/urls.py → apps/api/v1/urls.py)
   ↓
4. View Function (LoginAPIView in views.py)
   ↓
5. Serializer Validation (LoginSerializer in serializers.py)
   ↓
6. Database Query (User model)
   ↓
7. JWT Token Generation (djangorestframework-simplejwt)
   ↓
8. Response Serialization (UserSerializer)
   ↓
9. JSON Response to Client
```

---

## Security Layers

```
┌────────────────────────────────────────────┐
│  Layer 1: HTTPS (Production)              │
│  Encrypts all data in transit             │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│  Layer 2: JWT Token Authentication        │
│  Verifies user identity                   │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│  Layer 3: Permission Checks               │
│  Validates user access rights             │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│  Layer 4: Input Validation                │
│  Serializers validate all data            │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│  Layer 5: Database Security               │
│  SQL injection protection, etc.           │
└────────────────────────────────────────────┘
```

---

## API Versions (Future)

```
/api/
├── v1/                    ← Current (Stable)
│   ├── auth/
│   ├── assets/           ← Coming soon
│   └── locations/        ← Coming soon
│
├── v2/                    ← Future (Breaking changes)
│   └── (Not yet)
│
└── docs/                  ← Documentation
    ├── swagger/
    └── redoc/
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Production Setup                     │
└─────────────────────────────────────────────────────────┘

┌──────────────┐
│   Nginx      │  ← Reverse Proxy, SSL Termination
│   (443/80)   │
└──────┬───────┘
       │
       ├─────────────┬────────────────┐
       │             │                │
       ▼             ▼                ▼.





┌──────────┐  ┌──────────┐    ┌──────────┐
│  Django  │  │  Django  │    │  Django  │
│  Server  │  │  Server  │    │  Server  │
│  (8000)  │  │  (8001)  │    │  (8002)  │
└────┬─────┘  └────┬─────┘    └────┬─────┘
     │            │               │
     └────────────┼───────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   PostgreSQL    │
         │    Database     │
         └─────────────────┘
```

---

## Technology Stack

```
┌─────────────────────────────────────────────┐
│  Frontend (Any)                             │
│  • React / Vue / Angular                    │
│  • Mobile Apps (iOS/Android)                │
│  • Third-party integrations                 │
└─────────────────┬───────────────────────────┘
                  │ REST API (JSON)
┌─────────────────▼───────────────────────────┐
│  Backend (Python/Django)                    │
│  • Django 6.0.1                             │
│  • Django REST Framework                    │
│  • djangorestframework-simplejwt            │
│  • drf-yasg (Swagger)                       │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│  Database                                   │
│  • SQLite (Development)                     │
│  • PostgreSQL (Production)                  │
└─────────────────────────────────────────────┘
```

---

## Next Phase Planning

```
Current Phase (COMPLETED ✅)
├── User Authentication
├── Login/Logout
├── Registration
├── Profile Management
└── Password Management

Phase 2 (NEXT) 📋
├── Asset Management APIs
│   ├── List Assets
│   ├── Create Asset
│   ├── Update Asset
│   ├── Delete Asset
│   └── Search/Filter
│
├── Asset Details
│   ├── Depreciation info
│   ├── Transfer history
│   └── Maintenance records
│
└── File Upload
    └── Asset images

Phase 3 (FUTURE) 📋
├── Location APIs
├── Reports APIs
└── Advanced Features
```

---

## Testing Strategy

```
┌─────────────────────────────────────────────┐
│  1. Interactive Testing                     │
│     • Swagger UI (http://localhost:8000/    │
│       api/docs/)                            │
│     • ReDoc (http://localhost:8000/api/     │
│       redoc/)                               │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  2. Automated Testing                       │+
│     • test_api_login.py                     │
│     • Python unittest                       │
│     • pytest (future)                       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  3. Manual Testing                          │
│     • Postman collection                    │
│     • cURL commands                         │
│     • Browser fetch/axios                   │
└─────────────────────────────────────────────┘
```

---

## Summary Stats

``` 
📊 Project Statistics (Phase 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Files Created:         11
✅ API Endpoints:          8
✅ Serializers:            4
✅ Views:                  6
✅ Documentation:          5 
✅ Test Files:             2

📦 Dependencies Added:     2
🔒 Auth Methods:           3 (JWT, Session, Basic)
📖 Doc Pages:              2 (Swagger, ReDoc)
⏱️  Token Lifetime:       1h (Access), 7d (Refresh)

🎯 Status: PHASE 1 COMPLETE ✅
```
