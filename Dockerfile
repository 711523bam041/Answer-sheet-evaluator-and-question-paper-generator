# ---------- Build React frontend ----------
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ---------- Python + Tesseract backend ----------
FROM python:3.11-slim

WORKDIR /app

# Install Tesseract OCR and required system libraries
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/requirements.txt

RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy built React frontend from first stage
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Verify Tesseract exists during build
RUN tesseract --version

ENV PYTHONPATH=/app/backend

EXPOSE 10000

CMD ["sh", "-c", "gunicorn --chdir backend --bind 0.0.0.0:${PORT:-10000} app:app"]