# 🚀 QUICK START GUIDE

## Installation & Setup

### Prerequisites Check
```bash
# Check Python
python --version  # Should be 3.11+

# Check Node
node --version    # Should be 18+

# Check Docker (if using Docker)
docker --version
docker-compose --version
```

### Option A: Docker (Fastest Way)

```bash
# 1. Navigate to project
cd d:\answer-evaluator

# 2. Create environment files
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env

# 3. Start all services
docker-compose up --build

# Wait for all services to start (~1-2 minutes first time)
# Look for: "answer-evaluator-backend  | * Running on"
# Look for: "answer-evaluator-frontend | ready in"

# 4. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
# Database: localhost:5432 (user: evaluator, pass: evaluator123)
```

### Option B: Local Development

#### Backend Setup:
```bash
# 1. Navigate to backend
cd d:\answer-evaluator\backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env from example
copy .env.example .env

# 6. Run Flask app
python app.py

# Should see: * Running on http://127.0.0.1:5000
```

#### Frontend Setup (New Terminal):
```bash
# 1. Navigate to frontend
cd d:\answer-evaluator\frontend

# 2. Install dependencies
npm install

# 3. Create .env from example
copy .env.example .env

# 4. Start development server
npm run dev

# Should see: http://localhost:5173 (or 5174)
```

## Testing the Application

### 1. Create Test Account

**In Browser:**
1. Go to `http://localhost:3000` (or `http://localhost:5173` for local dev)
2. Click "Create a new account"
3. Enter:
   - Username: `testuser`
   - Password: `test123!`
   - Confirm Password: `test123!`
4. Click "Create Account"
5. You'll be redirected to Login

### 2. Login

1. Enter credentials:
   - Username: `testuser`
   - Password: `test123!`
2. Click "Sign in"
3. You should be redirected to Dashboard

### 3. Test Upload & Evaluation

**Option A: Using Sample Files**

The project includes test files:
- `demo_answer_key.txt` - Answer key
- `demo_student_answer.txt` - Student answer

1. On Dashboard, upload:
   - Answer Key: `demo_answer_key.txt`
   - Student Answer: `demo_student_answer.txt`
   - Student Name: "John Doe"

2. Click "Start Evaluation"
3. Watch progress bar (should reach 100%)
4. You'll be redirected to Results

**Option B: Using Your Own Files**

Create test files:
```
# answer_key.pdf or answer_key.txt
Question: What is the capital of France?
Answer: The capital of France is Paris.

# student_answer.pdf or student_answer.txt
The capital of France is Paris, which is located in northern France.
```

### 4. Verify Results

You should see:
- ✅ Student name displayed
- ✅ Score calculated (should be high for similar answer)
- ✅ Similarity percentage
- ✅ Feedback (e.g., "Highly Similar")
- ✅ Status (Clear/Flagged)

### 5. Test Download

1. Click "CSV" to download results
2. Click "PDF" to download report
3. Files should download with name `evaluation_results.csv` or `.pdf`

### 6. Test Data Preservation

1. Upload new files for another student
2. Go back to Results
3. **Verify**: First student's results are STILL there
4. You should see both students in the table

This proves the **data loss bug is fixed**! ✅

## Testing API Directly

### Health Check
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "message": "API is running",
  "database": "connected"
}
```

### Get Results (Need Token)
```bash
# 1. Login to get token
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123!"}'

# Copy the access_token from response

# 2. Use token to get results
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:5000/api/results
```

## Checking Logs

### Backend Logs

**Using Docker:**
```bash
docker-compose logs -f backend
```

**Local Development:**
```bash
# Check log file
type backend\logs\app.log  # Windows
tail -f backend/logs/app.log  # macOS/Linux
```

You should see entries like:
```
2024-01-15 10:30:45,123 - flask - INFO - Logging initialized at level INFO
2024-01-15 10:31:12,456 - flask - INFO - Database initialized successfully
2024-01-15 10:31:25,789 - flask - INFO - New user registered: testuser
2024-01-15 10:31:35,012 - flask - INFO - User logged in: testuser
```

## Troubleshooting

### Docker Won't Start
```bash
# Check logs
docker-compose logs

# Rebuild everything
docker-compose down
docker-compose up --build

# Or clean everything and restart
docker-compose down -v
docker-compose up --build
```

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### Frontend Can't Connect to Backend
1. Check backend is running: `curl http://localhost:5000/api/health`
2. Check frontend `.env` has correct `VITE_API_URL`
3. Check Docker network: `docker network ls`

### Database Connection Error
```bash
# Check PostgreSQL container
docker-compose ps db

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### File Upload Fails
- Check max file size: Default is 50MB in `.env`
- Verify file type is allowed (pdf, png, jpg, jpeg, txt)
- Check file isn't empty
- Check disk space available

## Performance Notes

### First Time Startup
- Tesseract OCR needs to initialize (~5 seconds)
- SentenceTransformer model loads on first evaluation (~10 seconds)
- Subsequent evaluations are much faster

### Large Files
- 10MB PDF: ~30 seconds
- 20 student files: ~2-3 minutes
- Plagiarism check scales with O(n²)

## Next Steps

1. **Explore the Code:**
   - Backend: `d:\answer-evaluator\backend\app.py`
   - Frontend: `d:\answer-evaluator\frontend\src`
   - Check `.env.example` files for all available options

2. **Customize:**
   - Change plagiarism threshold: `PLAGIARISM_THRESHOLD=0.85`
   - Increase file size limit: `MAX_FILE_SIZE=104857600`
   - Change logging level: `LOG_LEVEL=DEBUG`

3. **Deploy:**
   - See README.md for deployment options
   - IMPLEMENTATION_SUMMARY.md for next steps

4. **Report Issues:**
   - Check backend logs: `backend/logs/app.log`
   - Frontend console errors: Press F12
   - Docker logs: `docker-compose logs`

## Support Files

- 📖 `README.md` - Full documentation
- 📋 `IMPLEMENTATION_SUMMARY.md` - What was improved
- 🔧 `backend/.env.example` - Backend configuration
- 🔧 `frontend/.env.example` - Frontend configuration

---

**Status: Ready to Test!** ✅

Need help? Check the logs first! 📝
