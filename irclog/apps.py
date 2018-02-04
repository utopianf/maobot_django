from django.apps import AppConfig


class IrclogConfig(AppConfig):
    name = 'irclog'

    def ready(self):
        """register the signal to post log to irc"""
