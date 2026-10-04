# image for the api. docker compose builds it with build .
FROM python:3.12-slim

# dont write pyc files,print logs straight to the terminal.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# install packages first so this layer stays cached.
# changing app code will not install packages again,only requirements.txt will.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

EXPOSE 8000

# normal start. docker compose replaces this with --reload while developing.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
