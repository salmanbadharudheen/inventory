# API Quick Start Guide

## Installation

1. **Install new dependencies:**
```bash
pip install djangorestframework djangorestframework-simplejwt drf-yasg
```

Or use the updated requirements.txt:
```bash
pip install -r requirements.txt
```

2. **Run migrations:**
```bash
python manage.py migrate
```

3. **Start the server:**
```bash
python manage.py runserver
```

## Quick Test

### 1. Create a superuser (if not already created):
```bash
python manage.py createsuperuser
```

### 2. Test the Login API:

**Using cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"your_password\"}"
```

**Using Browser/Postman:**
- URL: `http://localhost:8000/api/v1/auth/login/`
- Method: POST
- Body (JSON):
```json
{
    "username": "admin",
    "password": "your_password"
}
```

### 3. Access Interactive Documentation:
- Swagger: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/` | API root |
| POST | `/api/v1/auth/login/` | User login |
| POST | `/api/v1/auth/register/` | User registration |
| POST | `/api/v1/auth/logout/` | User logout |
| GET | `/api/v1/auth/profile/` | Get user profile |
| PUT | `/api/v1/auth/profile/` | Update profile |
| POST | `/api/v1/auth/change-password/` | Change password |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |

## Response Example

**Login Success:**
```json
{
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "ADMIN"
    },
    "tokens": {
        "access": "eyJ0eXAiOiJKV1Qi...",
        "refresh": "eyJ0eXAiOiJKV1Qi..."
    },
    "message": "Login successful"
}
```

## Using the Access Token

Add the token to your request headers:
```
Authorization: Bearer <your_access_token>
```

## Project Structure

```
apps/
└── api/
    ├── __init__.py
    ├── apps.py
    ├── urls.py
    └── v1/
        ├── __init__.py
        ├── serializers.py
        ├── views.py
        └── urls.py
```

## Next Steps

1. ✅ User Authentication API (Complete)
2. 📋 Assets API (Next)
3. 📋 Locations API
4. 📋 Reports API

For detailed documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
