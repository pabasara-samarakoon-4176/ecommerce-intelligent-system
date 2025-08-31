FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
EXPOSE 10001
WORKDIR /app
COPY . .
RUN uv sync
CMD ["uv", "run", "agent/", "--host", "0.0.0.0", "--port", "10001"]