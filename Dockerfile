FROM python:3.10-slim

# Instalar FFmpeg y dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para evitar warnings de permisos
RUN useradd -m appuser && mkdir /app && chown appuser:appuser /app
USER appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip==25.0.1
RUN pip install --no-cache-dir -r Requirements.txt

CMD ["python", "main.py"]
