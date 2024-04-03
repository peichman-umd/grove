#!/usr/bin/env python
"""Server startup script."""
import os

from grove import settings
from grove.wsgi import application

from waitress import serve

if __name__ == '__main__':
    serve(application, host=settings.SERVER_HOST, port=settings.SERVER_PORT)
