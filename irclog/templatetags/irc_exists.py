from django import template
from django.core.files.storage import default_storage

register = template.Library()


@register.filter(name='irc_exists')
def irc_exists(path):
    return default_storage.exists(path)
