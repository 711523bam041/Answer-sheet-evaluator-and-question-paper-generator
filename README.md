# AI-Powered Automatic Answer Sheet Evaluation System

A production-ready web application for automatic evaluation of student answer sheets using AI-powered OCR and semantic similarity analysis, with built-in plagiarism detection.

## 🎯 Key Features

### Core Functionality
- **AI-Powered Evaluation**: Uses OCR (Tesseract) to extract text from PDFs/images and semantic similarity (Sentence Transformers) to score answers
- **Plagiarism Detection**: Automatically flags student answers with >80% similarity (configurable)
- **Student Identification**: Associate each answer sheet with student names
- **Real-time Processing**: Batch evaluation with progress indicators
- **Export Options**: Download results as CSV or PDF reports
- **Result History**: Keep all evaluation results organized by batch

### Authentication & Security
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Users can only access their own evaluation results
- **Password Security**: Bcrypt password hashing
- **File Validation**: Size limits, type checking, and security scanning
- **Request Validation**: Input sanitization and validation

### User Interface
- **Modern React Frontend**: Clean, professional design inspired by Medium
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Drag-and-drop Upload**: Intuitive file upload with preview
- **Student Name Input**: Associate files with student names during upload
- **Interactive Tables**: Sortable, filterable results with search functionality
- **Toast Notifications**: Real-time feedback for all user actions
- **Progress Indicators**: Upload and processing progress tracking
- **Loading States**: Proper loading and empty states throughout

### Performance & Reliability
- **Efficient Processing**: Image compression and optimized text extraction
- **Error Handling**: Comprehensive error handling with fallback mechanisms
- **Logging System**: Detailed logging for debugging and monitoring
- **Request Timeout**: Configurable timeouts to prevent hanging requests
- **Health Checks**: Built-in health check endpoints
- **Database Indexes**: Optimized database queries

## 🏗️ Project Structure

```
answer-evaluator/
├── backend/
│   ├── app.py                 # Main Flask application (500+ lines, production-ready)
│   ├── models.py              # Database models with timestamps and cascading
│   ├── evaluator.py           # OCR + AI evaluation logic
│   ├── validators.py          # Request validation functions
│   ├── logger.py              # Logging configuration
│   ├── config.py              # Configuration management
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile             # Production-grade container config
│   ├── .env.example          # Environment variables template
│   ├── uploads/              # Student file uploads
│   └── logs/                 # Application logs
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main app (improved error handling, timeout management)
│   │   ├── pages/
│   │   │   ├── Login.jsx     # Authentication page
│   │   │   ├── Register.jsx  # User registration
│   │   │   ├── Dashboard.jsx # Enhanced with student names, progress
│   │   │   └── Results.jsx   # Improved table with student info
│   │   ├── components/
│   │   │   ├── Layout.jsx    # Sidebar navigation
│   │   │   └── ProtectedRoute.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile            # Multi-stage build for production
│   ├── .env.example
│   └── postcss.config.js
│
├── docker-compose.yml         # Complete stack (backend, frontend, PostgreSQL, networks)
├── .env.example              # Root environment variables
└── README.md                 # This file
```

## 📋 Tech Stack

### Backend
- **Framework**: Python Flask 3.0+
- **Database**: PostgreSQL 15 (with SQLite fallback)
- **ORM**: SQLAlchemy
- **Authentication**: JWT (Flask-JWT-Extended)
- **OCR**: PyTesseract + Tesseract-OCR
- **AI/ML**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Password**: Bcrypt
- **Server**: Gunicorn
- **Logging**: Python logging with rotation

### Frontend
- **Framework**: React 18.2
- **Build Tool**: Vite 5.0
- **Styling**: Tailwind CSS 3.3
- **HTTP Client**: Axios 1.6
- **Routing**: React Router v6
- **Notifications**: react-hot-toast
- **Icons**: Lucide React

### DevOps
- **Containerization**: Docker & Docker Compose
- **Production Server**: Gunicorn + Nginx (ready)
- **Database**: PostgreSQL with persistent volumes
- **Health Checks**: Built-in health endpoints

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (recommended)
- OR Python 3.11+ and Node.js 18+
- Tesseract OCR (for local development)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd answer-evaluator

# Create .env file from example
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Start all services
docker-compose up --build

# Services will be available at:
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
# Database: localhost:5432
```

### Option 2: Local Development

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Initialize database and run
python app.py
```

**Frontend Setup (new terminal):**
```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start development server
npm run dev
```

Access the application at `http://localhost:5173`

## 📝 API Documentation

### Authentication

**Register**
```
POST /api/register
Body: { "username": "user", "password": "pass123" }
Response: { "message": "Registration successful", "username": "user" }
```

**Login**
```
POST /api/login
Body: { "username": "user", "password": "pass123" }
Response: { "access_token": "jwt-token", "username": "user", "user_id": 1 }
```

### Upload & Evaluation

**Upload Answer Sheets**
```
POST /api/upload (JWT Required)
FormData:
  - answerkey: File (PDF/Image/Text)
  - answers: File[] (Multiple files)
  - studentNames[0]: "John Doe"
  - studentNames[1]: "Jane Smith"
  
Response: {
  "message": "Evaluation complete",
  "batch_id": "uuid",
  "results_count": 2,
  "results": [
    {
      "filename": "...",
      "similarity": 85.5,
      "marks": 100,
      "remark": "Excellent Similarity",
      "is_flagged": false
    }
  ]
}
```

### Results

**Get Results**
```
GET /api/results?batch_id=optional (JWT Required)
Response: [
  {
    "id": 1,
    "student_name": "John Doe",
    "filename": "john_answer.pdf",
    "marks": 85,
    "similarity": 85.5,
    "feedback": "Highly Similar",
    "flagged": false,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

**Download CSV**
```
GET /api/download_csv?batch_id=optional (JWT Required)
Response: CSV file with all results
```

**Download PDF**
```
GET /api/download_pdf?batch_id=optional (JWT Required)
Response: PDF file with formatted report
```

### Health

**Health Check**
```
GET /api/health
Response: { "status": "ok", "message": "API is running", "database": "connected" }
```

## ⚙️ Configuration

### Backend Configuration (`.env`)

```env
# Flask
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
# Or for SQLite: DATABASE_URL=sqlite:///app.db

# File Upload
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=52428800  # 50MB
KEEP_UPLOADED_FILES=false

# Evaluation
PLAGIARISM_THRESHOLD=0.80  # 80%
MIN_SIMILARITY_PERCENTAGE=0.0

# Logging
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Frontend Configuration (`.env`)

```env
VITE_API_URL=http://localhost:5000
VITE_APP_NAME=Answer Evaluator
VITE_REQUEST_TIMEOUT=30000  # 30 seconds
```

## 🔒 Security Features

- ✅ JWT token-based authentication
- ✅ Bcrypt password hashing (cost factor: 12)
- ✅ CORS properly configured
- ✅ Input validation and sanitization
- ✅ File type and size validation
- ✅ SQL injection protection (via SQLAlchemy)
- ✅ XSS prevention
- ✅ Secure filename handling
- ✅ Request timeout protection
- ✅ Non-root Docker user

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE user (
  id INTEGER PRIMARY KEY,
  username VARCHAR(150) UNIQUE NOT NULL,
  password VARCHAR(150) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Results Table
```sql
CREATE TABLE result (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL FOREIGN KEY,
  batch_id VARCHAR(36) NOT NULL INDEX,
  student_name VARCHAR(255) NOT NULL,
  student_filename VARCHAR(255) NOT NULL,
  marks FLOAT NOT NULL,
  similarity_score FLOAT NOT NULL,
  feedback VARCHAR(500) NOT NULL,
  is_flagged BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW() INDEX,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🧪 Testing

### Manual API Testing

```bash
# Using curl or Postman

# Register
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Health check
curl http://localhost:5000/api/health
```

### Test Files

Sample test files are provided in:
- `demo_answer_key.txt` - Example answer key
- `demo_student_answer.txt` - Example student answer
- `test_api.py` - Python API test script

```bash
python test_api.py
```

## 📦 Deployment

### Docker Compose (Development/Staging)

```bash
docker-compose up -d
```

### Kubernetes / Cloud Deployment

The application is designed to be cloud-native:

**Environment Variables for Production:**
```env
FLASK_ENV=production
SECRET_KEY=<generate-secure-key>
JWT_SECRET_KEY=<generate-secure-key>
DATABASE_URL=<cloud-database-url>
LOG_LEVEL=WARNING
```

**Recommended Platforms:**
- ☁️ Render (Full stack support)
- 🚂 Railway (Docker support)
- 🎯 AWS (ECS + RDS)
- 🔵 Azure (Container Instances + PostgreSQL)

## 🐛 Troubleshooting

### Tesseract Not Found
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose ps

# Rebuild and restart
docker-compose down
docker-compose up --build
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
# Or kill existing process
lsof -ti:5000 | xargs kill -9
```

### CORS Issues
- Ensure `VITE_API_URL` matches backend URL
- Check `CORS_ORIGINS` in backend `.env`

## 📈 Performance Optimization

- Image compression before OCR
- Database query indexing
- JWT token caching
- Lazy model loading (SentenceTransformers)
- Efficient text extraction
- Optimized plagiarism comparison algorithm

## 🔄 Updates & Maintenance

### Regular Tasks
- Monitor logs: `docker-compose logs -f backend`
- Backup database: `docker-compose exec db pg_dump ...`
- Update dependencies: `pip list --outdated`, `npm outdated`

### Monitoring

Logs are stored in:
- Backend: `./backend/logs/app.log`
- Docker: `docker-compose logs`

## 📝 License

MIT License - See LICENSE file for details

## 👥 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Email: support@evaluator.app
- Documentation: See [DOCS.md](./DOCS.md)

## 🎉 Acknowledgments

- Tesseract OCR Community
- Sentence-Transformers Team
- Flask & SQLAlchemy
- React & Vite Communities
# Build images
docker build -t answer-evaluator-backend ./backend
docker build -t answer-evaluator-frontend ./frontend

# Push to container registry (Docker Hub, etc.)
docker tag answer-evaluator-backend your-registry/answer-evaluator-backend
docker tag answer-evaluator-frontend your-registry/answer-evaluator-frontend
docker push your-registry/answer-evaluator-backend
docker push your-registry/answer-evaluator-frontend
```

### Deploy to Render

1. **Create Render Services**:
   - Create a PostgreSQL database on Render
   - Create a Web Service for the backend
   - Create a Static Site for the frontend

2. **Backend Configuration**:
   - Build Command: `./build.sh` (create script to install Python deps)
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - Environment Variables:
     ```
     SECRET_KEY=your-secret-key
     JWT_SECRET_KEY=your-jwt-secret-key
     DATABASE_URL=postgresql://...
     ```

3. **Frontend Configuration**:
   - Build Command: `npm run build`
   - Publish Directory: `dist`
   - Environment Variables:
     ```
     VITE_API_URL=https://your-backend-url.onrender.com/api
     ```

### Deploy to Railway

1. **Create Railway Project**:
   - Connect your GitHub repository
   - Railway will auto-detect the project structure

2. **Configure Services**:
   - Backend: Python service with `requirements.txt`
   - Frontend: Node.js service with build command
   - Database: PostgreSQL

3. **Environment Variables**:
   Set the same variables as above in Railway dashboard

## API Documentation

### Authentication Endpoints
- `POST /api/register` - User registration
- `POST /api/login` - User login (returns JWT token)

### Protected Endpoints (require Authorization header)
- `POST /api/upload` - Upload answer key and student answers
- `GET /api/results` - Get evaluation results
- `GET /api/download_csv` - Download results as CSV
- `GET /api/download_pdf` - Download results as PDF

## Usage

1. **Register/Login**: Create an account or sign in
2. **Upload Files**: 
   - Upload the answer key (PDF/Image)
   - Upload student answer sheets (multiple files supported)
3. **Evaluation**: The system will process files and show results
4. **Review Results**: View scores, feedback, and flagged plagiarism cases
5. **Export**: Download results in CSV or PDF format

## Configuration

### Environment Variables

**Backend (.env)**:
```
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/database
```

**Frontend (.env)**:
```
VITE_API_URL=http://localhost:5000/api
```

### Database Setup

For production, use PostgreSQL. For development, SQLite is configured by default.

## Troubleshooting

### Common Issues

1. **OCR not working**: Ensure Tesseract is installed
2. **Database connection failed**: Check DATABASE_URL format
3. **Frontend API calls failing**: Verify VITE_API_URL is correct
4. **Build failures**: Ensure all dependencies are listed in requirements.txt/package.json

### Performance Optimization

- Image compression before OCR processing
- Batch processing for multiple files
- Caching of evaluation results
- Database indexing on user_id and timestamps

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
3. Connect your repository.
4. During setup, fill these fields:
   - **Environment:** Docker
   - **Branch:** main
5. Under **Advanced**, add Environment Variables:
   - `SECRET_KEY` = `<Generate a secure random string>`
   - `FLASK_ENV` = `production`
   - *Note:* If you want persistent Database, create a "PostgreSQL" instance on Render first, then copy its "Internal Database URL" and paste it as the `DATABASE_URL` variable.
6. Click **Create Web Service**.

### Deploying to Railway
1. Push this repository to GitHub.
2. Go to [Railway Dashboard](https://railway.app), click **New Project** -> **Deploy from GitHub repo**.
3. Choose your repository.
4. Add a Database: Click **New** -> **Database** -> **Add PostgreSQL**.
5. Go to your Web Service **Variables** tab, and add:
   - `SECRET_KEY` = `<Generate a secure random string>`
   - `FLASK_ENV` = `production`
6. Under **Settings**, Railway should automatically detect the `Dockerfile`. Deploy the project!

## Project Structure
- `app.py`: The main Flask routing and database configuration logic.
- `evaluator.py`: AI components handling OCR and Answer Semantic Evaluation / Plagiarism checking.
- `models.py`: Database models definition via Flask-SQLAlchemy.
- `templates/`: Contains HTML files featuring modern layouts.
- `static/`: Contains `style.css` for beautiful UI.
- `requirements.txt`: Python package dependencies for production and development.
- `Dockerfile` / `docker-compose.yml`: For containerized orchestrating.
