FROM python:3.12.1-bullseye

ENV PYTHONOPTIMIZE=1
ENV TZ=Europe/Moscow

WORKDIR /usr/src/app

COPY . .

RUN python -m pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi \
    && rm -rf $(poetry config cache-dir)/{cache,artifacts}

RUN useradd -r -UM app
USER app

CMD ["python3", "main.py"]