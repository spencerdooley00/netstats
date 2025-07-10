FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y gcc \
 && python -m venv /opt/venv \
 && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY ./templates ./templates
COPY ./static ./static
COPY ./scripts ./scripts
COPY ./nba_on_court ./nba_on_court
COPY application.py .
EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "application:application"]
