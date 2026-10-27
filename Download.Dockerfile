FROM python:3.12-slim

WORKDIR /app

COPY analysis/download_cool_seq_tool_files.py .

RUN python -m pip install --upgrade "pip>=26.2.2" \
    && python -m pip install boto3

VOLUME /wags_tails
