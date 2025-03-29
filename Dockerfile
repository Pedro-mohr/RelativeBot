FROM python:3.10-slim

# Instalar dependencias del sistema y FFmpeg
RUN apt-get update && apt-get install -y ffmpeg git

# Configurar el entorno de trabajo
WORKDIR /app

# Copiar archivos necesarios
COPY Requirements.txt .
COPY main.py .
COPY webserver.py .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Usar la variable de entorno PORT para Flask
ENV PORT=8000

# Comando de inicio (NO se define en la UI de Render)
CMD ["python", "main.py"]