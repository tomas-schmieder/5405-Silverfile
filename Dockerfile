FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SILVERFILE_VAR_DIR=/data SILVERFILE_ENABLE_NATIVE_OCR=1 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false
# OpenCV (used by the built-in OCR) needs libGL and glib at runtime
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 1000 silverfile && mkdir -p /data && chown -R silverfile:silverfile /app /data
USER silverfile
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
