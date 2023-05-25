FROM python:3-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1  
ARG DockerHome="/app"

RUN mkdir -p $DockerHome

RUN pip install --upgrade pip

COPY req.txt req.txt

RUN pip install -r req.txt


COPY . ${PATH}
WORKDIR ${PATH}


CMD [ "python3", "testbot.py" ]





