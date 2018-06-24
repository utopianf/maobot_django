import datetime
import os
import subprocess
import uuid

from django import forms
from django.core.files import File
from django.utils import timezone

from ircimages.models import Image
from .models import Log

DEFAULT_START_AT = timezone.now() - datetime.timedelta(hours=3)
DEFAULT_END_AT = timezone.now()
INPUT_FORMATS = ['%Y-%m-%dT%H:%M:%S']


class LogCreateForm(forms.ModelForm):
    """Form to create log with image."""

    class Meta:
        model = Log
        fields = ('channel', 'nick', 'command', 'message', 'attached_image')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_irc = False
        instance.is_from_log = True

        # handle attached image
        img_temp = self.cleaned_data.get('attached_image')
        if img_temp:
            image = Image(related_log=instance)
            image.image.save(str(uuid.uuid4()).replace('-', ''), File(img_temp))
            instance.attached_image = image.thumb
        if commit:
            instance.save()
        return instance
