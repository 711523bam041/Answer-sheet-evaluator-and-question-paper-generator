import requests
import json
import os

# 1. Login to get token
print("Logging in to get JWT token...")
login_response = requests.post(
    'http://localhost:5000/api/login',
    json={'username': 'testuser', 'password': 'test123'}
)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

token = login_response.json()['access_token']
headers = {
    'Authorization': f'Bearer {token}'
}

# 2. Prepare files for upload
answer_key_path = 'sample_answer_key.pdf'
student_answer_path = 'sample_student_answer.pdf'

if not os.path.exists(answer_key_path) or not os.path.exists(student_answer_path):
    print("Sample PDF files not found. Run create_sample_pdfs.py first.")
    exit(1)

print("\nUploading files for evaluation...")
files = [
    ('answerkey', (os.path.basename(answer_key_path), open(answer_key_path, 'rb'), 'application/pdf')),
    ('answers', (os.path.basename(student_answer_path), open(student_answer_path, 'rb'), 'application/pdf'))
]

data = {
    'studentNames[0]': 'John Doe'
}

response = requests.post(
    'http://localhost:5000/api/upload',
    headers=headers,
    files=files,
    data=data
)

print(f"Status: {response.status_code}")
try:
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception:
    print(f"Raw Response: {response.text}")
