FROM python:3.10-alpine3.19
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN apk update && apk add clang
RUN pip3 install --upgrade pip && pip3 install --user --no-warn-script-location pipenv
WORKDIR /usr/local/app/
COPY Pipfile* ./
RUN python3 -m pipenv install --system --deploy --dev
COPY . ./
ENV PACKAGE_VERSION 1
RUN python3 setup.py install

