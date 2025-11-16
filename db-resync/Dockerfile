FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Cliente MySQL para poder usar mysqldump y mysql
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*

RUN pip install mysql-connector-python

COPY resync.py .

CMD ["python", "resync.py"]
