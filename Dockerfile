# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster

MAINTAINER market_shoppers

WORKDIR /opt/app
COPY /requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

ENV FLASK_APP=/opt/app/src
ENV PLAID_ENV=sandbox
ENV PLAID_PRODUCTS=auth,transactions,investments
ENV PLAID_COUNTRY_CODES=US,CA
ENV PLAID_REDIRECT_URI=http://localhost:5000/

EXPOSE 5000
ENTRYPOINT ["python"]
CMD ["-m", "flask", "run", "--port=5000"]
