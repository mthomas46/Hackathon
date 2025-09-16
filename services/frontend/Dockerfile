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
FROM python:3.12-slim

# Set working directory
WORKDIR /app/services/frontend

# Install required Python packages
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic aiofiles

# Copy Python application files
COPY *.py ./
COPY config.yaml ./
COPY modules/ ./modules/

# Copy built Elm assets from builder stage
COPY --from=elm-builder /app/static/ ./static/

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/health')"

# Start the FastAPI application
CMD ["python", "main.py"]
