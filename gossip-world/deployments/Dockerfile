# FROM python:3
FROM python:3.11

WORKDIR /app
ADD app/requirements.txt /app/requirements.txt
# RUN pip install -r requirements.txt
RUN pip install --no-cache-dir --default-timeout=100 --retries=10 -r requirements.txt
CMD python routes.py
