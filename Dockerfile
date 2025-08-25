FROM public.ecr.aws/docker/library/python:3.11-slim

# System deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port and set defaults expected by the app
ENV PORT=8080 \
    AWS_DEFAULT_REGION=us-east-1 \
    DD_SERVICE=my-bedrock-proxy \
    DD_ENV=dev

# Start via ddtrace-run
CMD ["ddtrace-run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

