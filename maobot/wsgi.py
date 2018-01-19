"""
WSGI config for maobot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

import sys
sys.path.append('/home/django_project/maobot')
sys.path.append('/home/django_project/maobot/maobot')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maobot.settings")

application = get_wsgi_application()
