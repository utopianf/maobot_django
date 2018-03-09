import atexit
import signal
import shutil
import sys
import os
from pathlib import Path

from irc3.plugins.command import command
from irc3.plugins.cron import cron
import irc3


@irc3.plugin
class MyPlugin:
    """A plugin is a class which take the IrcBot as argument
    """

    requires = [
        'irc3.plugins.core',
        'irc3.plugins.userlist',
        'irc3.plugins.command',
        'irc3.plugins.human',
        'irc3.plugins.async',
    ]

    def __init__(self, bot):
        self.bot = bot
        self.log = bot.log

    def connection_made(self):
        """triggered when connection is up"""

    def server_ready(self):
        """triggered after the server sent the MOTD (require core plugin)"""

    def connection_lost(self):
        """triggered when connection is lost"""

    @irc3.event(irc3.rfc.JOIN)
    def welcome(self, mask, channel, **kw):
        """Welcome people who join a channel"""
        if mask.nick != self.bot.nick:
            self.bot.call_with_human_delay(
                self.bot.privmsg, channel, 'ようこそ〜 %s!' % mask.nick)
        else:
            self.bot.call_with_human_delay(
                self.bot.privmsg, channel, "どうも〜")

    @cron('* * * * *')
    @irc3.asyncio.coroutine
    def get_users(self):
        """Check who is in the channel each minute"""
        result = yield from self.bot.async_cmds.whois(nick=self.bot.nick)
        for channel in Channel.objects.all():
            userstr = ", ".join([u for u in self.bot.channels[channel.name] if u != ''])
            channel.ircusers = userstr
            channel.save()

    @irc3.event(irc3.rfc.TOPIC)
    @irc3.event(irc3.rfc.RPL_TOPIC)
    def get_topic(self, channel=None, data=None, **kw):
        """Check topic"""
        channel = Channel.objects.get(name__exact=channel)
        channel.topic = data
        channel.save()

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, mask=None, data=None, target=None, **kw):
        try:
            channel = Channel.objects.get(name__exact=target)
            nick = mask.split('!')[0]
            Log(nick=nick, message=data, channel=channel).save()
        except:
            pass

    @command
    def join(self, mask, target, args):
        """Join command

            %%join <channel>...
        """
        try:
            channel = args['<channel>'][0]
            self.bot.join(channel)
            Channel(name=channel).save()
        except:
            pass

    @command
    def part(self, mask, target, args):
        """Part command

           %%part <channel>...
        """
        try:
            channel = args['<channel>'][0]
            self.bot.part(channel)
            Channel.objects.get(name__exact=channel).delete()
        except:
            pass


def goodbye():
    shutil.rmtree('/tmp/run/irc3')
    os.remove('./media/ircon')
    print("Goodbye.")


atexit.register(goodbye)
signal.signal(signal.SIGTERM, goodbye)
signal.signal(signal.SIGINT, goodbye)


def main():
    # instanciate a bot
    Path('media/ircon').touch()
    channels = [c.name for c in Channel.objects.all()]
    #channels = ['#maobot_test']
    config = {
        'nick': 'maobot_test', 'autojoins': channels,
        'host': 'irc.ircnet.ne.jp', 'port': 6667, 'ssl': False,
        'encoding': 'ISO-2022-JP',
        'includes': [
            'irc3.plugins.core',
            'irc3.plugins.command',
            'irc3.plugins.human',
            'irc3.plugins.fifo',
            'irc3.plugins.userlist',
            'irc3.plugins.async',
            __name__,  # this register MyPlugin
        ],
        'irc3.plugins.fifo': {'runpath': '/tmp/run/irc3'}
    }
    bot = irc3.IrcBot.from_config(config)
    bot.run(forever=True)


if __name__ == '__main__':
    sys.path.append('.')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maobot.settings')
    import django
    django.setup()
    from irclog.models import Log, Channel
    main()
