FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
COPY entrypoint.sh .
RUN mkdir -p /data
ENV BOOKHUB_DATA_DIR=/data
EXPOSE 8000
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
