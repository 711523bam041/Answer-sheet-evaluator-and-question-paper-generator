import requests
import json

# Test registration
print("Testing registration endpoint...")
response = requests.post(
    'http://localhost:5000/api/register',
    json={'username': 'testuser', 'password': 'test123'}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test login
print("\nTesting login endpoint...")
response = requests.post(
    'http://localhost:5000/api/login',
    json={'username': 'testuser', 'password': 'test123'}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
