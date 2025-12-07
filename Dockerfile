# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Optimize MoviePy/ImageMagick
ENV MOVIEPY_THREADS=1
ENV IMAGEMAGICK_BINARY=/usr/bin/convert

# Install system dependencies (FFmpeg is required)
# Install system dependencies (FFmpeg and ImageMagick are required)
RUN apt-get update && apt-get install -y ffmpeg imagemagick && rm -rf /var/lib/apt/lists/*


# Copy requirements
COPY requirements.txt .

# Fix ImageMagick policy to allow text operations and limit memory usage to prevent OOM
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="resource" name="memory" value="256MiB"\/>/<policy domain="resource" name="memory" value="256MiB"\/>/g' /etc/ImageMagick-6/policy.xml || true

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Render sets PORT env var, but we document it essentially)
EXPOSE 8000

# Run the app using the PORT environment variable provided by Render (default 10000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
