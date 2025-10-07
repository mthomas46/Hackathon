FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8014

# Run application (use simple version temporarily)
CMD ["uvicorn", "main_simple:app", "--host", "0.0.0.0", "--port", "8014"]

