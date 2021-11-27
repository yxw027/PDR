FROM python:3.8.3-slim-buster AS base

RUN apt-get update
RUN apt-get install -y netcat

# Dedicated Workdir for App
WORKDIR /pdr

# Do not run as root
RUN useradd -m -r pdr && \
    chown pdr/pdr

COPY requirements.txt /pdr
# RUN pip3 install -r requirements.txt

FROM base AS src
COPY . /pdr

# install pyrobomogen here as a python package
RUN pip3 install .

COPY scripts/docker-entrypoint.sh /entrypoint.sh

# Use the `pdr` binary as Application
FROM src AS prod

# this is add to fix the bug related to permission
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]

CMD ["pdr", "-c", "config.yaml"]