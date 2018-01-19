import datetime
import os
import re
import subprocess

from django.contrib.auth.mixins import LoginRequiredMixin
from django.dispatch import Signal
from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import generic

from .models import Channel, Log
from .forms import ChannelSwitchForm, LogCreateForm, LogSearchForm

from ircimages.models import Image

# Create your views here.
class IndexView(LoginRequiredMixin, generic.CreateView):
    template_name = 'irclog/index.html'
    model = Log
    form_class = LogCreateForm
    success_url = reverse_lazy('irclog:index')

    login_url = 'accounts:login'
    redirect_field_name = 'redirect_to'

    def get_context_data(self, **kwargs):
        #init setting
        end_at = timezone.now()
        start_at = timezone.now() - datetime.timedelta(hours=3)
        channel = Channel.objects.all()[0]

        #LogCreateForm
        create_form = LogCreateForm(self.request.POST)
        if create_form.is_valid():
            start_at = timezone.now() - datetime.timedelta(hours=3)
            end_at   = timezone.now()
            channel = create_form.cleaned_data.get('channel')

        #SearchLogForm
        keyword = ''
        search_form = LogSearchForm(self.request.GET)
        if search_form.is_valid():
            start_at = search_form.cleaned_data.get('start_at')
            end_at   = search_form.cleaned_data.get('end_at')
            channel = search_form.cleaned_data.get('search_channel')
            keyword = search_form.cleaned_data.get('keyword')

            duration = end_at - start_at
            if 'next_duration' in self.request.GET:
                end_at += duration
                start_at += duration
            elif 'previous_duration' in self.request.GET:
                end_at -= duration
                start_at -= duration
            elif 'now' in self.request.GET:
                end_at = timezone.now()
                start_at = timezone.now() - datetime.timedelta(hours=3)

        qs = Log.objects.filter(created_at__range=(start_at, end_at)
             ).filter(message__contains=keyword).order_by('created_at')

        # Make context
        context = super(IndexView, self).get_context_data(**kwargs)
        context['log_list'] = qs
        try:
            context['channel'] = channel
        except:
            context['channel'] = Channel.objects.all()[0]

        context['search_form'] = search_form
        #context['create_form'] = create_form
        context['end_at'] = end_at.strftime('%Y-%m-%dT%H:%M:%S')
        context['start_at'] = start_at.strftime('%Y-%m-%dT%H:%M:%S')
        context['channels'] = Channel.objects.all()
        context['current_user'] = self.request.user
        return context

    def form_valid(self, form):
        """
        Send message to IRC and save the pic and video.
        """
        super(IndexView, self).form_valid(form)
        if form.is_valid():
            message = form.cleaned_data.get('message')
            command = form.cleaned_data.get('command')
            channel = form.cleaned_data.get('channel')
            sendstr = "%s %s :(%s) %s" % (command, channel,
                               form.cleaned_data.get('nick'),
                               form.cleaned_data.get('message'))
            cmd = "echo '%s' > /tmp/run/irc3/:raw" % sendstr
            if os.path.isdir("/tmp/run/irc3"):
                subprocess.call(cmd, shell=True)

        return self.render_to_response(self.get_context_data(form=form))

