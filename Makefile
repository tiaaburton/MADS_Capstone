FLASK_APP = src/__init__.py
FLASK := FLASK_APP=$(FLASK_APP) env/bin/flask

setup: requirements.txt
	pip install -r requirements.txt

