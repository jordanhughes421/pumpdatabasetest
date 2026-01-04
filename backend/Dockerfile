FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code into a subdirectory so that 'backend' package imports work
COPY . backend/

# Set PYTHONPATH to include /app so that 'backend' package is importable
ENV PYTHONPATH=/app

# Run the application
# We use host 0.0.0.0 to be accessible from outside the container
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
