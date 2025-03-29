FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libssl3 \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r Requirements.txt

CMD ["python", "main.py"]
