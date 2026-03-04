# SPDX-FileCopyrightText: GitHub, Inc.
# SPDX-License-Identifier: MIT

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash coreutils python3 python3-pip curl wget git ca-certificates \
    file binutils xxd \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
