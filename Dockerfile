FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR .

RUN pip install poetry
COPY poetry.lock pyproject.toml ./
RUN poetry export --without-hashes --ansi -f requirements.txt > requirements.txt | pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
