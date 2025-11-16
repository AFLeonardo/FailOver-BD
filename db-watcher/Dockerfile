FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN pip install mysql-connector-python

COPY watcher.py .

CMD ["python", "watcher.py"]
