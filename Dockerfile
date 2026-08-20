# Dashboard image — serves the Flask report viewer on the public internet.
# Build:  docker build -t auditor-dashboard .
# Run :   docker run -p 8080:8080 -v $(pwd)/data:/app/data auditor-dashboard
# Deploy: fly deploy   (uses fly.toml in this repo)

FROM python:3.11-slim

WORKDIR /app

# Install the auditor and its dashboard extras.
COPY pyproject.toml README.md LICENSE ./
COPY auditor ./auditor
RUN pip install --no-cache-dir -e ".[dashboard]" "gunicorn==23.0.0"

# Bring sample reports so the live URL renders something on first hit.
COPY data ./data
COPY specs ./specs

ENV FLASK_APP=auditor.dashboard.app:app \
    PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "auditor.dashboard.app:app"]
