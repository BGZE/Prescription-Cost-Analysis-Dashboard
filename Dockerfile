# Multi-stage build: compile the React frontend, then serve it + the API
# from one FastAPI/uvicorn process. This single image is what Render deploys.

# --- Stage 1: build the frontend -------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: python backend -----------------------------------------------
FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Backend deps
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r backend/requirements.txt

# App code
COPY backend/ ./backend/
COPY etl/ ./etl/
# Built SPA (served by FastAPI from ../frontend/dist relative to backend/app)
COPY --from=frontend /app/frontend/dist ./frontend/dist

# Render provides $PORT. Default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
