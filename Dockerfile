# Use slim Python image
FROM python:3.11-slim

# Install system dependencies for mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config netcat-openbsd curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Prevent Python from writing pyc and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Python deps first (caches better)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Entrypoint
RUN chmod +x docker/entrypoint.sh
ENTRYPOINT ["docker/entrypoint.sh"]

EXPOSE 8000

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
