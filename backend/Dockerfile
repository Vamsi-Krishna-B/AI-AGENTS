FROM python:3.11-slim

# System deps for MoviePy / Pillow / ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libmagic1 \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv export --frozen --format requirements.txt --no-hashes --no-emit-project --output-file /tmp/requirements.txt \
    && uv pip install --system --no-cache -r /tmp/requirements.txt

COPY . .

# Create storage directories
RUN mkdir -p storage/videos/raw storage/videos/final storage/audio storage/thumbnails assets/music

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
