# --- Stage 1: Install dependencies ---
# Using a separate stage for deps means if your code changes but
# requirements.txt doesn't, Docker reuses the cached layer (fast rebuilds).
FROM python:3.12-slim AS deps

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Production image ---
FROM python:3.12-slim

WORKDIR /app

# Create a non-root user (security best practice — if the app gets
# compromised, the attacker doesn't have root inside the container)
RUN addgroup --system app && adduser --system --ingroup app app

# Copy installed packages from the deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Switch to non-root user
USER app

EXPOSE 8000

# --workers 2: run 2 Uvicorn workers to handle concurrent requests
# In K8s later, we'll scale with replicas instead of workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
