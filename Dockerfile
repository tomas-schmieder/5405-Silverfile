FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SILVERFILE_VAR_DIR=/data SILVERFILE_ENABLE_NATIVE_OCR=0 LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 1000 silverfile && mkdir -p /data && chown -R silverfile:silverfile /app /data
USER silverfile
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
