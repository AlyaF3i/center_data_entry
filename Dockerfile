# 1. Base image
FROM python:3.10-slim

# 2. Avoid .pyc files & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. System dependencies (e.g. for Postgres)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         build-essential \
         libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Set working dir
WORKDIR /app

# 5. Install Python deps early for layer caching
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 6. Copy app code + your Excel file + entrypoint
COPY . .

# 7. Make entrypoint executable (in case your repo lost the +x bit)
RUN chmod +x ./entrypoint.sh

# 8. Expose HTTP port
EXPOSE 8000

# 9. Run our entrypoint
ENTRYPOINT ["./entrypoint.sh"]
