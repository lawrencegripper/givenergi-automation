FROM python:3.10

WORKDIR /app
COPY requirements.txt .

RUN pip install -r requirements.txt
COPY . .

ENTRYPOINT [ "python" ]

LABEL org.opencontainers.image.source https://github.com/lawrencegripper/givenergy-automation