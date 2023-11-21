FROM ubuntu:22.04

# install deps
RUN apt update && \
    apt install -y build-essential python3.10 python3.10-dev python3.10-venv libpq-dev
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
