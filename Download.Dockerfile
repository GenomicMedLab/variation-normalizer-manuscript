FROM python:3.12-slim

WORKDIR /app

COPY analysis/download_cool_seq_tool_files.py .

RUN pip install boto3

VOLUME /wags_tails
