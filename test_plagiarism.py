import requests
import json
import os
import shutil

# Remove copy if it exists from previous failed run
if os.path.exists('sample_student_answer_copy.pdf'):
    try:
        os.remove('sample_student_answer_copy.pdf')
    except Exception:
        pass

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

# 2. Copy the student answer to simulate a duplicate submission
shutil.copy('sample_student_answer.pdf', 'sample_student_answer_copy.pdf')

answer_key_path = 'sample_answer_key.pdf'
student1_path = 'sample_student_answer.pdf'
student2_path = 'sample_student_answer_copy.pdf'

print("\nUploading files to test plagiarism detection (2 identical student answers)...")

# Open files using with-statement to ensure they are closed afterwards
with open(answer_key_path, 'rb') as f1, open(student1_path, 'rb') as f2, open(student2_path, 'rb') as f3:
    files = [
        ('answerkey', (os.path.basename(answer_key_path), f1, 'application/pdf')),
        ('answers', (os.path.basename(student1_path), f2, 'application/pdf')),
        ('answers', (os.path.basename(student2_path), f3, 'application/pdf'))
    ]

    data = {
        'studentNames[0]': 'John Doe',
        'studentNames[1]': 'Jane Doe'
    }

    response = requests.post(
        'http://localhost:5000/api/upload',
        headers=headers,
        files=files,
        data=data
      )

# Now it is safe to remove the file as f3 is closed
if os.path.exists('sample_student_answer_copy.pdf'):
    os.remove('sample_student_answer_copy.pdf')

print(f"Status: {response.status_code}")
try:
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception:
    print(f"Raw Response: {response.text}")
