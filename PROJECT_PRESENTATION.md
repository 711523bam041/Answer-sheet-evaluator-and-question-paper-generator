# 📊 Project Presentation: AI-Powered Automatic Answer Sheet Evaluation & Plagiarism Detection System

This document outlines the core technical details, system architecture, features, and deployment configurations of the project. It can be used directly for a project review, demonstration, or slideshow presentation.

---

## 🚀 Executive Summary
An automated evaluation system designed for educational institutions to grade student answer sheets and detect copying. It integrates SBERT semantic analysis and Tesseract OCR to parse and evaluate both digital and scanned files, dramatically reducing grading latency and catching duplicate submissions instantly.

---

## 🛠️ Tech Stack & Technologies

### 1. Frontend
* **Core:** React (v18.2) + Vite (for lightning-fast build and dev reload)
* **Styling:** Tailwind CSS (modern, clean, and responsive sidebar layout)
* **HTTP Client:** Axios (custom request/response interceptors to manage JWT authorization headers and timeout buffers)
* **Icons:** Lucide React

### 2. Backend
* **Framework:** Python Flask (decoupled REST API structure)
* **WSGI Production Server:** Gunicorn (2-worker setup with a 5-minute timeout configuration)
* **Database ORM:** SQLAlchemy (Flask-SQLAlchemy)
* **Authentication:** JWT (Flask-JWT-Extended) tokens for secure sessions
* **Password Hashing:** Bcrypt (safe password encryption in database)

### 3. Artificial Intelligence & NLP
* **OCR Text Extraction:** PyTesseract (Tesseract OCR wrapper) for image/scanned PDF reading
* **PDF Render Engine:** PyMuPDF (`fitz`) for rasterizing scanned PDFs into page-by-page images to run OCR
* **Semantic Analysis:** Sentence Transformers SBERT (`all-MiniLM-L6-v2`) for encoding answers into 384-dimensional dense vectors
* **Scoring Metrics:** Cosine Similarity comparing student dense vectors to answer key dense vectors

---

## 🏗️ System Architecture & Workflow

### 1. Document ingestion
- User uploads an Answer Key and multiple Student Answers via React dashboard.
- Files undergo server-side validation (file size limits, supported mime-types like `.pdf`, `.png`, `.jpg`, `.txt`, `.docx`).

### 2. Text Extraction (OCR & PDF Fallback)
- **Digital PDF:** Directly extracts text using `PyPDF2` (extremely fast).
- **Scanned PDF/Images:** Automatically renders PDF pages to images using `PyMuPDF`, performs contrast enhancement/noise reduction, and extracts text via Tesseract OCR.

### 3. AI Evaluation Engine
- Translates extracted student text and key text into semantic vector embeddings.
- Computes **Cosine Similarity**. The score is normalized with a **Length Penalty** (to prevent short/blank answers or keyword padding from manipulating the AI).
- Assigns grades and generates qualitative remarks (e.g., *"Excellent"*, *"Partially Correct"*, *"No Match"*).

### 4. Plagiarism Detection Engine
- Performs pairwise cosine similarity comparisons between all student answer vector embeddings (O(N²) complexity, optimized with embedding caching).
- Submissions exceeding **80% similarity** (threshold configurable via environment variables) are flagged as plagiarized in the database, showing exact match percentages in the UI.

---

## 🗄️ Database Design (SQLAlchemy ORM)

### 1. User Model
* Secure authentication mapping.
* Cascading relationships: deleting a user purges their evaluation history.

### 2. Result Model
* **batch_id (UUID):** Groups evaluations together so historical uploads are preserved and easily searchable.
* **student_name:** Tracks student identification.
* **marks & similarity_score:** Stores grade metrics.
* **confidence_score:** Displays the AI's confidence in extraction/evaluation.
* **feedback:** Qualitative assessment text.
* **is_flagged:** Boolean plagiarism status.

---

## 🔒 Security & Performance Features
- **JWT Protection:** Token-based authorization ensures users only see their own results.
- **Strict Input Validation:** Protects endpoints against SQL Injection (via ORM parameterization), XSS, path traversal, and malicious file uploads (verifying extensions and empty files).
- **Graceful Timeouts:** Increased frontend Axios and backend Gunicorn timeouts (to 5 minutes) to ensure heavy initial AI downloads or OCR rendering don't cause connection drops.
- **Rate Limiting:** Protects resources from brute-force request floods.

---

## 💾 Deployment & Devops
* **Docker Support:** Fully containerized backend (Flask/Gunicorn) and frontend (Nginx/Serve) with a `docker-compose.yml` specifying service health checks and a PostgreSQL database container.
* **Railway & Render Ready:** Out-of-the-box configuration with `.env` templates and postgres migration checks.
