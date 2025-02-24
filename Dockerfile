FROM python:3.10
#Zeitzone für den Sync zwischen Divera und Stein
ENV TZ=Europe/Berlin
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update
#fehlende python3 module und Timezone Data
RUN apt install -y tzdata python3-httpx python3-h2

WORKDIR /app
COPY divera.py .
COPY steinapi.py .
ENTRYPOINT ["./divera.py"]