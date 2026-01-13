FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code into a 'backend' directory to preserve package structure
# This matches the expected import structure (e.g., 'from backend.database import ...')
COPY . backend/

# Add /app to PYTHONPATH so 'backend' package is resolvable
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
