# syntax=docker/dockerfile:1
FROM python:3.9.15-buster

MAINTAINER market_shoppers

WORKDIR /opt/app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install numpy
RUN pip install -r requirements.txt --no-cache
COPY . .

ENV FLASK_APP=src/__init__.py
ENV FLASK_ENV=development
ENV PLAID_ENV=sandbox
ENV PLAID_PRODUCTS=auth,transactions,investments
ENV PLAID_COUNTRY_CODES=US,CA
ENV PLAID_REDIRECT_URI=http://localhost:5000/
ENV OAUTHLIB_INSECURE_TRANSPORT=1

EXPOSE 5000
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5000"]
