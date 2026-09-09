FROM docker.io/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY example /app/example
COPY main.py /app/main.py

RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 8765

ENTRYPOINT ["/app/backend/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8765"]
