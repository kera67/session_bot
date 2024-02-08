FROM python:3.12.1-bullseye as builder

COPY . .

RUN pip install -U --no-cache-dir pip wheel setuptools==59.8.0 poetry

RUN poetry build -f wheel
RUN poetry export -f requirements.txt -o requirements.txt --without-hashes

RUN pip wheel -w dist -r requirements.txt


FROM python:3.12.1-bullseye as runtime

WORKDIR /usr/src/app

ENV PYTHONOPTIMIZE=1
ENV TZ=Europe/Moscow

COPY --from=builder dist dist
COPY --from=builder main.py ./

RUN pip install -U pip==20.2.4

RUN pip install --no-cache-dir --no-index dist/*.whl && \
    rm -rf dist

RUN useradd -r -UM app
USER app

CMD ["python", "main.py"]