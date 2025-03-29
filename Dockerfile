FROM python:3.10-slim
WORKDIR /app

# Descarga FFmpeg desde una fuente confiable
RUN apt-get update && apt-get install -y wget \
    && wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    && tar -xf ffmpeg-release-amd64-static.tar.xz \
    && mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && rm -rf ffmpeg-*

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]