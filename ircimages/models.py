import uuid

from django.db import models
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


# Create your models here.
def upload_path_handler(instance):
    return "%s.%s" % (str(uuid.uuid4()).replace('-', ''), instance.extension)


class Image(models.Model):
    """One single image"""
    original_url = models.URLField(null=True)
    related_log = models.ForeignKey('irclog.Log', related_name='images',
                                    null=True, on_delete=models.SET_NULL)
    caption = models.CharField('Caption', max_length=20, null=True)
    extension = models.CharField('Extension', max_length=10, null=True)
    image = models.ImageField(upload_to=upload_path_handler)
    thumb = ImageSpecField(source='image', processors=[ResizeToFill(150, 150)],
                           format='JPEG', options={'quality': 80})
    created_at = models.DateTimeField(default=timezone.now)
    image_set = models.ForeignKey('ImageSet', related_name='images',
                                  null=True, on_delete=models.SET_NULL)


class ImageSet(models.Model):
    """Multi images"""
    title = models.CharField('title', max_length=20)
