#!/bin/bash
export FLASK_APP=web/app
export PYTHONPATH=web/
pipenv run flask run
