import atexit
import datetime
import io
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


def goodbye():
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
        channel = Channel.objects.get(name__exact=e.target)
        nick = e.source.nick
        if nick == c.nickname:
            c.notice(e.target, 'どうも〜')
            Log(nick=nick, message='どうも〜', channel=channel, command='NOTICE').save()
        else:
            c.notice(e.target, '%sさん, ようこそ〜' % nick)
            Log(nick='maobot', message='%sさん, ようこそ〜' % nick, channel=channel, command='NOTICE').save()
            c.mode(e.target, '+o %s' % nick)


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
            opers = self.channels[ch].opers()
            ircusers = self.channels[ch].users()
            userlist = []
            for u in ircusers:
                if u in opers:
                    userlist.append('☆'+u)
                else:
                    userlist.append(u)
            channel.ircusers = ', '.join(userlist)
            channel.save()

        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(seconds=60)
        qs = Log.objects.filter(created_at__range=(start_time, end_time)).order_by('created_at')
        for log in qs:
            if not log.is_irc:
                if log.nick == 'maobot':
                    send_message = log.message
                else:
                    send_message = '(%s) %s' % (log.nick, log.message)
                if log.command == 'NOTICE':
                    self.connection.notice(log.channel.name, send_message)
                elif log.command == 'PRIVMSG':
                    self.connection.privmsg(log.channel.name, send_message)
        qs.update(is_irc=True)

def main():
    Path('media/ircon').touch()
    autojoins = [c.name for c in Channel.objects.all()]
    c = MaoBot(autojoins, 'maobot_test', 'irc.ircnet.ne.jp', 6667)
    c.start()

if __name__ == '__main__':
    main()
