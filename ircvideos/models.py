from django.db import models
from django.utils import timezone

# Create your models here.
class Video(models.Model):
    """One single video"""
    original_url = models.URLField()
    related_log = models.ForeignKey('irclog.Log', related_name='videos',
                                    null=True, on_delete=models.SET_NULL)
    title = models.CharField('Title', max_length=20)
    video = models.FileField()
    thumb = models.ImageField()
    created_at = models.DateTimeField(default=timezone.now)

