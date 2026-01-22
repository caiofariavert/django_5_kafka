SHELL:=/bin/bash
ARGS = $(filter-out $@,$(MAKECMDGOALS))
MAKEFLAGS += --silent
BASE_PATH=${PWD}
PYTHON_EXEC=python
VENV_PATH=~/venv/django-kafka

flake8:
	echo "verify pep8 ..."
	cd django_kafka && black . && isort . && flake8 .
	cd examples && black . && isort . && flake8 .

pip_install:
	docker-compose ${DOCKER_COMPOSE_FILE} exec app ${PYTHON_EXEC} -m pip install -r requirements.txt

create_venv:
	sudo apt-get install python3-dev python3-wheel python-dev gcc libpq-dev -y
	python3 -m venv ${VENV_PATH}
	${VENV_PATH}/bin/python -m pip install --upgrade pip setuptools wheel
	${VENV_PATH}/bin/pip install -r requeriments.txt

upgrade_packages: pip_install
	pip install pip-upgrade -y
	pip-upgrade --skip-virtualenv-check
