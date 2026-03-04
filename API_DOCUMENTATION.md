# API Development Guide

## Overview
This document provides comprehensive information about the Inventory Management System API.

## Base URL
- **Development**: `http://localhost:8000/api/`
- **Production**: `https://your-domain.com/api/`

## API Version
Current Version: **v1**

## Authentication

### JWT (JSON Web Token) Authentication

The API uses JWT tokens for authentication. After login, you'll receive an access token and a refresh token.

#### Token Types
- **Access Token**: Short-lived token (1 hour) used for API requests
- **Refresh Token**: Long-lived token (7 days) used to get new access tokens

#### Headers
Include the access token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

---

## Authentication Endpoints

### 1. User Login
**POST** `/api/v1/auth/login/`

Authenticate a user and receive JWT tokens.

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response (200 OK):**
```json
{
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "EMPLOYEE",
        "organization": 1,
        "branch": 2,
        "department": 3,
        "designation": "Software Engineer",
        "employee_id": "EMP001",
        "date_joined": "2024-01-15T10:30:00Z"
    },
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    },
    "message": "Login successful"
}
```

**Error Response (400 Bad Request):**
```json
{
    "non_field_errors": ["Invalid username or password."]
}
```

---

### 2. User Registration
**POST** `/api/v1/auth/register/`

Register a new user account.

**Request Body:**
```json
{
    "username": "new_user",
    "email": "user@example.com",
    "password": "secure_password123",
    "password2": "secure_password123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "EMPLOYEE",
    "organization": 1,
    "branch": 2,
    "department": 3,
    "designation": "Engineer",
    "employee_id": "EMP002"
}
```

**Response (201 Created):**
```json
{
    "user": {
        "id": 2,
        "username": "new_user",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "EMPLOYEE",
        ...
    },
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    },
    "message": "Registration successful"
}
```

---

### 3. User Logout
**POST** `/api/v1/auth/logout/`

Logout the current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (Optional):**
```json
{
    "refresh_token": "your_refresh_token"
}
```

**Response (200 OK):**
```json
{
    "message": "Logout successful"
}
```

---

### 4. Get User Profile
**GET** `/api/v1/auth/profile/`

Retrieve the current authenticated user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "EMPLOYEE",
        "organization": 1,
        "branch": 2,
        "department": 3,
        "designation": "Software Engineer",
        "employee_id": "EMP001",
        "date_joined": "2024-01-15T10:30:00Z"
    }
}
```

---

### 5. Update User Profile
**PUT** `/api/v1/auth/profile/`

Update the current user's profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@example.com",
    "designation": "Senior Engineer"
}
```

**Response (200 OK):**
```json
{
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john.smith@example.com",
        "first_name": "John",
        "last_name": "Smith",
        ...
    },
    "message": "Profile updated successfully"
}
```

---

### 6. Change Password
**POST** `/api/v1/auth/change-password/`

Change the current user's password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "old_password": "current_password",
    "new_password": "new_secure_password123",
    "new_password2": "new_secure_password123"
}
```

**Response (200 OK):**
```json
{
    "message": "Password changed successfully"
}
```

**Error Response (400 Bad Request):**
```json
{
    "old_password": ["Old password is incorrect."]
}
```

---

### 7. Refresh Access Token
**POST** `/api/v1/auth/token/refresh/`

Get a new access token using the refresh token.

**Request Body:**
```json
{
    "refresh": "your_refresh_token"
}
```

**Response (200 OK):**
```json
{
    "access": "new_access_token"
}
```

---

## User Roles

The system supports the following user roles:

| Role | Value | Description |
|------|-------|-------------|
| Admin | `ADMIN` | Full system access |
| Employee | `EMPLOYEE` | Standard user access |
| Checker/Manager | `CHECKER` | Can review and approve |
| Senior Manager | `SENIOR_MANAGER` | Higher approval authority |

---

## Error Responses

### Common HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required or token invalid
- **403 Forbidden**: User doesn't have permission
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Error Format
```json
{
    "field_name": ["Error message"],
    "detail": "Error description"
}
```

---

## Testing the API

### Using cURL

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

**Get Profile:**
```bash
curl -X GET http://localhost:8000/api/v1/auth/profile/ \
  -H "Authorization: Bearer your_access_token"
```

### Using Python (requests)

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login/',
    json={
        'username': 'admin',
        'password': 'your_password'
    }
)
data = response.json()
access_token = data['tokens']['access']

# Get Profile
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(
    'http://localhost:8000/api/v1/auth/profile/',
    headers=headers
)
print(response.json())
```

### Using JavaScript (fetch)

```javascript
// Login
fetch('http://localhost:8000/api/v1/auth/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        username: 'admin',
        password: 'your_password'
    })
})
.then(response => response.json())
.then(data => {
    const accessToken = data.tokens.access;
    
    // Get Profile
    return fetch('http://localhost:8000/api/v1/auth/profile/', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Interactive API Documentation

Visit these URLs for interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **API Root**: http://localhost:8000/api/v1/

---

## Next Steps for API Development

### Phase 2: Assets API
- List assets
- Create asset
- Update asset
- Delete asset
- Asset search and filtering

### Phase 3: Locations API
- Branches CRUD
- Departments CRUD
- Locations hierarchy

### Phase 4: Reports API
- Asset reports
- Depreciation reports
- Transfer reports

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (never in localStorage for sensitive apps)
3. **Implement token refresh** before expiry
4. **Validate all input data**
5. **Use rate limiting** to prevent abuse
6. **Log all API access** for audit trails

---

## Support

For API support or questions, contact the development team.

**Last Updated**: March 3, 2026
