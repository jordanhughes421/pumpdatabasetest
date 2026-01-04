FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the application
# We use host 0.0.0.0 to be accessible from outside the container
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
