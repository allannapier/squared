#!/bin/bash

# Create necessary directories
mkdir -p .vercel/output/static

# Copy static files
cp -r static/* .vercel/output/static/

# Copy templates
cp -r templates .vercel/output/
