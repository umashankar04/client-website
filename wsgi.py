"""WSGI entrypoint for hosted deployments."""

from main import create_app


app = create_app()