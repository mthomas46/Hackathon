FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5700

# Run application (use simple version temporarily)
CMD ["python", "-m", "uvicorn", "main_simple:app", "--host", "0.0.0.0", "--port", "5700"]

