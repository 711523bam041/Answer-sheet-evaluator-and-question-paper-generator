import requests
import json

BASE_URL = 'http://localhost:5000'

# Register
reg_data = {'username': 'testdebug', 'password': 'testpass123'}
reg_response = requests.post(f'{BASE_URL}/api/register', json=reg_data)
print(f"Register: {reg_response.status_code}")
print(f"Response: {reg_response.json()}\n")

# Login
login_data = {'username': 'testdebug', 'password': 'testpass123'}
login_response = requests.post(f'{BASE_URL}/api/login', json=login_data)
print(f"Login: {login_response.status_code}")
login_json = login_response.json()
print(f"Response: {login_json}")
token = login_json.get('access_token')
print(f"Token: {token}\n")

# Test /api/results with token
headers = {'Authorization': f'Bearer {token}'}
results_response = requests.get(f'{BASE_URL}/api/results', headers=headers)
print(f"Results (with token): {results_response.status_code}")
print(f"Response: {results_response.json()}\n")

# Test /api/results without token
results_response_no_token = requests.get(f'{BASE_URL}/api/results')
print(f"Results (without token): {results_response_no_token.status_code}")
print(f"Response: {results_response_no_token.json()}\n")
