# SPDX-FileCopyrightText: GitHub, Inc.
# SPDX-License-Identifier: MIT

FROM seclab-shell-base:latest
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap tcpdump tshark netcat-openbsd dnsutils curl jq httpie \
    && rm -rf /var/lib/apt/lists/*
