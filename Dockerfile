FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY backend.py /app/backend.py
RUN useradd --system --uid 10001 nexus && mkdir -p /data && chown -R nexus:nexus /app /data
USER nexus
EXPOSE 8000
CMD ["python", "-u", "backend.py"]
