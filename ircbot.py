import atexit
import datetime
import os
from pathlib import Path
import shutil
import signal
import sys
from irc.bot import SingleServerIRCBot

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maobot.settings')
import django
django.setup()

from irclog.models import Log, Channel


def goodbye(signum, frame):
    os.remove('./media/ircon')
    print("Goodbye.")


atexit.register(goodbye)
signal.signal(signal.SIGTERM, goodbye)
signal.signal(signal.SIGINT, goodbye)


class MaoBot(SingleServerIRCBot):
    def __init__(self, autojoins, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.connection.transmit_encoding = 'ISO-2022-JP'
        self.connection.buffer_class.encoding = 'ISO-2022-JP'
        self.autojoins = autojoins

    def on_welcome(self, c, e):
        for channel in self.autojoins:
            c.join(channel)
        self.reactor.scheduler.execute_every(3, self.echo_test)

    def on_join(self, c, e):
        if e.source.nick == c.nickname:
            c.privmsg(e.target, 'どうも〜')
        else:
            c.privmsg(e.target, '%s, ようこそ〜' % e.source.nick)

    def on_pubmsg(self, c, e):
        channel = Channel.objects.get(name__exact=e.target)
        message = e.arguments[0]
        Log(nick=e.source.nick, message=message, channel=channel).save()

    def on_pubnotice(self, c, e):
        channel = Channel.objects.get(name__exact=e.target)
        message = e.arguments[0]
        Log(nick=e.source.nick, message=message, command='NOTICE',
            channel=channel).save()

    def echo_test(self):
        for ch in self.autojoins:
            channel = Channel.objects.get(name__exact=ch)
            channel.ircusers = ", ".join(self.channels[ch].users())
            channel.save()

        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(seconds=10)
        qs = Log.objects.filter(created_at__range=(start_time, end_time))
        for log in qs:
            if not log.is_irc:
                send_message = '(%s) %s' % (log.nick, log.message)
                self.connection.privmsg(log.channel.name, send_message)
        qs.update(is_irc=True)

def main():
    Path('media/ircon').touch()
    autojoins = [c.name for c in Channel.objects.all()]
    c = MaoBot(autojoins, 'maobot_test', 'irc.ircnet.ne.jp', 6667)
    c.start()

if __name__ == '__main__':
    main()
