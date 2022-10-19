FLASK_APP = backend
FLASK := FLASK_APP=$(FLASK_APP) env/bin/flask

.PHONY: run
run:
    FLASK_ENV=sandbox $(FLASK) run

.PHONY: run-dev
run-production:
    FLASK_ENV=development $(FLASK) run