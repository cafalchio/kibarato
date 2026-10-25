.PHONY: setup dev check collectstatic

setup:
	uv sync --locked
	.venv/bin/python manage.py migrate --settings=config.settings_dev

dev:
	.venv/bin/python manage.py runserver 127.0.0.1:8000 --settings=config.settings_dev

check:
	.venv/bin/python manage.py check --settings=config.settings_dev

collectstatic:
	.venv/bin/python manage.py collectstatic --noinput --settings=config.settings
