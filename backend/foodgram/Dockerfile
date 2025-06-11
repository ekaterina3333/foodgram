FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей SSL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libssl-dev \
    openssl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "foodgram.wsgi", "--bind", "0.0.0.0:8000"] 