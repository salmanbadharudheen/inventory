"""
Test script for the API Login endpoint
Run this after starting the Django server with: python manage.py runserver
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_api_root():
    """Test API root endpoint"""
    print("\n" + "="*50)
    print("Testing API Root")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200


def test_login(username, password):
    """Test login endpoint"""
    print("\n" + "="*50)
    print("Testing Login API")
    print("="*50)
    
    url = f"{BASE_URL}/auth/login/"
    data = {
        "username": username,
        "password": password
    }
    
    print(f"URL: {url}")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data)
    print(f"\nStatus Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        return response.json()
    return None


def test_profile(access_token):
    """Test profile endpoint with authentication"""
    print("\n" + "="*50)
    print("Testing Profile API")
    print("="*50)
    
    url = f"{BASE_URL}/auth/profile/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"URL: {url}")
    print(f"Headers: Authorization: Bearer {access_token[:20]}...")
    
    response = requests.get(url, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    return response.status_code == 200


def test_invalid_login():
    """Test login with invalid credentials"""
    print("\n" + "="*50)
    print("Testing Invalid Login")
    print("="*50)
    
    url = f"{BASE_URL}/auth/login/"
    data = {
        "username": "invalid_user",
        "password": "wrong_password"
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    return response.status_code == 400


def main():
    print("\n" + "="*60)
    print("INVENTORY MANAGEMENT SYSTEM - API TEST SUITE")
    print("="*60)
    
    # Test 1: API Root
    print("\n1. Testing API Root endpoint...")
    if test_api_root():
        print("✅ API Root test passed")
    else:
        print("❌ API Root test failed")
    
    # Test 2: Invalid Login
    print("\n2. Testing Invalid Login...")
    if test_invalid_login():
        print("✅ Invalid Login test passed (correctly rejected)")
    else:
        print("❌ Invalid Login test failed")
    
    # Test 3: Valid Login (Replace with your actual credentials)
    print("\n3. Testing Valid Login...")
    username = input("\nEnter username (or press Enter to skip): ").strip()
    
    if username:
        password = input("Enter password: ").strip()
        
        result = test_login(username, password)
        
        if result:
            print("✅ Login test passed")
            
            # Test 4: Profile with Authentication
            access_token = result['tokens']['access']
            print("\n4. Testing Profile endpoint with authentication...")
            if test_profile(access_token):
                print("✅ Profile test passed")
            else:
                print("❌ Profile test failed")
        else:
            print("❌ Login test failed")
    else:
        print("⏭️  Skipping login and profile tests")
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)
    print("\nTo test more features:")
    print("- Visit Swagger UI: http://localhost:8000/api/docs/")
    print("- Visit ReDoc: http://localhost:8000/api/redoc/")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Make sure the Django server is running:")
        print("   python manage.py runserver")
    except Exception as e:
        print(f"\n❌ Error: {e}")
