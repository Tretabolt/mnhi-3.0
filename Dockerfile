FROM python:3.11-slim

RUN useradd -m -u 10001 mnhi_user
WORKDIR /app

COPY pyproject.toml CLAUDE.MD ./
COPY src ./src
COPY tests ./tests

RUN chown -R mnhi_user:mnhi_user /app
USER mnhi_user

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"]
