FROM python:3-bullseye

WORKDIR /app
COPY requirements.txt .

RUN pip install -r requirements.txt
COPY . .

ENTRYPOINT [ "python" ]

LABEL org.opencontainers.image.source https://github.com/lawrencegripper/givenergy-automation