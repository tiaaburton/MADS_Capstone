# syntax=docker/dockerfile:1
FROM python:3.9.15-slim-buster

MAINTAINER market_shoppers

RUN apk add --no-cache --update \
    python3 python3-dev gcc \
    gfortran musl-dev pip3 pip

ADD requirements-pip.txt .
RUN pip3 install --upgrade pip setuptools && \
    pip3 install -r requirements.txt

WORKDIR /opt/app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

ENV FLASK_APP=src/__init__.py
ENV FLASK_ENV=development
ENV PLAID_ENV=sandbox
ENV PLAID_PRODUCTS=auth,transactions,investments
ENV PLAID_COUNTRY_CODES=US,CA
ENV PLAID_REDIRECT_URI=http://localhost:5000/
ENV OAUTHLIB_INSECURE_TRANSPORT=1

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
EXPOSE 5000
