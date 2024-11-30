#!/bin/bash

# Install system dependencies
apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    build-essential \
    libjpeg-dev \
    zlib1g-dev

# Install Python dependencies
pip install -r requirements.txt
