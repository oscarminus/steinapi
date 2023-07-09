FROM python:3.10
RUN apt update
RUN apt install -y python3-requests

WORKDIR /app
COPY divera.py .
COPY steinapi.py .
ENTRYPOINT ./divera.py
