FROM docker/compose:debian-1.29.1

RUN sed -i -e 's/deb.debian.org/archive.debian.org/g' \
           -e 's|security.debian.org|archive.debian.org/|g' \
           -e '/stretch-updates/d' /etc/apt/sources.list \
    && apt update \
    && apt install -y curl
