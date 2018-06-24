import uuid

from django.db import models
from django.utils import timezone


# Create your models here.


def upload_path_handler(instance):
    return "%s.%s" % (str(uuid.uuid4()).replace('-', ''), instance.extension)


class Image(models.Model):
    """One single image"""

    original_url = models.URLField(null=True)
    related_log = models.ForeignKey('irclog.Log', related_name='images',
                                    null=True, on_delete=models.SET_NULL)
    caption = models.TextField('Caption', max_length=1000, null=True)
    extension = models.CharField('Extension', max_length=10, null=True)
    image = models.ImageField(null=True)
    thumb = models.ImageField(upload_to='thumb/',null=True)
    created_at = models.DateTimeField(default=timezone.now)
    image_set = models.ForeignKey('ImageSet', related_name='images',
                                  null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-created_at']


class Tag(models.Model):
    name = models.TextField('Tag', max_length=50)


class ImageSet(models.Model):
    """Multi images"""
    title = models.CharField('title', max_length=20)
