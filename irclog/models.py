from django.db import models
from django.utils import timezone

# Create your models here.


class Channel(models.Model):
    name = models.CharField('channel name', max_length=50, unique=True)
    topic = models.TextField('channel topic', null=True)
    ircusers = models.CharField('channel user', max_length=100, null=True)

    def __str__(self):
         return self.name


class Log(models.Model):
    AVAILABLE_COMMAND = (
        ('PRIVMSG', 'priv'),
        ('NOTICE', 'notice'),
    )
    command = models.CharField('irc command', max_length=10,
                               choices=AVAILABLE_COMMAND,
                               default='PRIVMSG')
    channel = models.ForeignKey(
        'Channel', null=True, on_delete=models.SET_NULL, default=1)
    nick = models.CharField('irc nick', max_length=20, default="test")
    message = models.CharField('irc message', max_length=500)
    attached_image = models.ImageField(
        'attached image', null=True, blank=True)
    created_at = models.DateTimeField('date created', default=timezone.now)
    is_irc = models.BooleanField(default=True)
    is_from_log = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return '%s [%s] %s: %s' % (
                self.created_at.strftime('%Y-%m-%d %H:%M:%S'), 
                self.channel, self.nick, self.message)

