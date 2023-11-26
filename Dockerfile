FROM ubuntu:22.04

# install deps
RUN apt-get update && apt-get install -y \
    libpq5 \
    python3.10 \
    python3.10-venv \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# copy only the requirements, to avoid invalidating the cache
COPY requirements.txt .
# install python deps
RUN python3 -m venv venv && \
    venv/bin/pip install -r requirements.txt

# copy & install rest of the app
COPY . .
RUN venv/bin/pip install .

WORKDIR /conf
CMD ["/app/venv/bin/gunicorn", "-c", "eio_userdb_gunicorn.conf.py"]
