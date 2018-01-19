import datetime
import uuid

from django import forms
from django.core.files import File
from django.forms import widgets
from django.utils import timezone

from .models import Channel, Log
from ircimages.models import Image

DEFAULT_START_AT = timezone.now()-datetime.timedelta(hours=3)
DEFAULT_END_AT   = timezone.now()
INPUT_FORMATS = ['%Y-%m-%dT%H:%M:%S']

class LogCreateForm(forms.ModelForm):
    """Form to create log with image."""
    #attached_image = Image()

    class Meta:
        model = Log
        fields = ('channel', 'nick', 'command', 'message', 'attached_image')


    def save(self, commit=True):
        instance = super().save(commit=False)
        img_temp = self.cleaned_data.get('attached_image')
        if img_temp:
            image = Image(related_log=instance)
            image.image.save(str(uuid.uuid4()).replace('-',''), File(img_temp))
            instance.attached_image = image.thumb
        if commit:
            instance.save()
        return instance

class LogSearchForm(forms.Form):
    start_at = forms.DateTimeField(
                  initial=DEFAULT_START_AT,
                  input_formats=INPUT_FORMATS)
    end_at   = forms.DateTimeField(
                  initial=DEFAULT_END_AT,
                  input_formats=INPUT_FORMATS)
    keyword  = forms.CharField(required=False)
    search_channel = forms.ModelChoiceField(Channel.objects.all(),
                  widget=forms.HiddenInput())


class ChannelSwitchForm(forms.Form):
    start_at = forms.DateTimeField(
                  initial=DEFAULT_START_AT,
                  input_formats=INPUT_FORMATS,
                  widget=forms.HiddenInput())
    end_at   = forms.DateTimeField(
                  initial=DEFAULT_START_AT,
                  input_formats=INPUT_FORMATS,
                  widget=forms.HiddenInput())
    switch_to_channel = forms.ModelChoiceField(Channel.objects.all())
