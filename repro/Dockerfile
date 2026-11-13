FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates cmake ninja-build pkg-config libsqlite3-dev libssl-dev \
    nlohmann-json3-dev libzstd-dev libopencv-dev libtiff-dev libcurl4-openssl-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
