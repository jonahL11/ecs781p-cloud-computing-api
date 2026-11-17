# Get python images and uv binaries
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


COPY . /app
WORKDIR /app

# set up venv and make it discoverable
RUN uv sync
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5050
CMD ["python" , "src/app.py"]