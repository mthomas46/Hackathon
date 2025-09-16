# Multi-stage build for Elm frontend service
FROM node:18-alpine as elm-builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json ./

# Install npm dependencies (includes elm toolchain)
RUN npm install

# Copy Elm project files
COPY elm.json ./
COPY src/ ./src/
COPY tests/ ./tests/

# Build the Elm application
RUN npm run build

# Production stage with Python FastAPI backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies and install
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt || echo "No requirements.txt found"

# Copy Python application files
COPY *.py ./
COPY config.yaml ./
COPY modules/ ./modules/

# Copy built Elm assets from builder stage
COPY --from=elm-builder /app/static/ ./static/

# Create a simple requirements.txt if it doesn't exist
RUN echo "fastapi==0.104.1\nuvicorn[standard]==0.24.0\naiofiles==23.2.1" > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
