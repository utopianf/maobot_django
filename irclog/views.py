import datetime
from datetime import datetime as dt
import os
import subprocess
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from .forms import LogCreateForm, LogSearchForm
from .models import Channel, Log


# Create your views here.
class IndexView(LoginRequiredMixin, generic.CreateView):
    template_name = 'irclog/index.html'
    model = Log
    form_class = LogCreateForm
    success_url = reverse_lazy('irclog:index')

    login_url = 'accounts:login'
    redirect_field_name = 'redirect_to'

    def get_context_data(self, **kwargs):
        # init setting
        end_at = timezone.now()
        start_at = timezone.now() - datetime.timedelta(hours=3)
        channel = Channel.objects.all()[0]

        # LogCreateForm
        create_form = LogCreateForm(self.request.POST)
        if create_form.is_valid():
            start_at = timezone.now() - datetime.timedelta(hours=3)
            end_at = timezone.now()
            channel = create_form.cleaned_data.get('channel')

        # SearchLogForm
        keyword = ''
        #search_form = LogSearchForm(self.request.GET)
        #if search_form.is_valid():
        #    start_at = search_form.cleaned_data.get('start_at')
        #    end_at = search_form.cleaned_data.get('end_at')
        #    channel = search_form.cleaned_data.get('search_channel')
        #    keyword = search_form.cleaned_data.get('keyword')

        #    duration = end_at - start_at
        #    if 'next_duration' in self.request.GET:
        #        end_at += duration
        #        start_at += duration
        #    elif 'previous_duration' in self.request.GET:
        #        end_at -= duration
        #        start_at -= duration
        #    elif 'now' in self.request.GET:
        #        end_at = timezone.now()
        #        start_at = timezone.now() - datetime.timedelta(hours=3)

        qs = Log.objects.filter(created_at__range=(start_at, end_at)
                                ).filter(message__contains=keyword).order_by('created_at')

        # Make context
        context = super(IndexView, self).get_context_data(**kwargs)
        context['log_list'] = qs
        try:
            context['channel'] = channel
        except NameError:
            context['channel'] = Channel.objects.all()[0]

        # context['search_form'] = search_form
        # context['create_form'] = create_form
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
            command = form.cleaned_data.get('command')
            channel = form.cleaned_data.get('channel')
            sendstr = "%s %s :(%s) %s" % (command, channel,
                                          form.cleaned_data.get('nick'),
                                          form.cleaned_data.get('message'))
            cmd = "echo '%s' > /tmp/run/irc3/:raw" % sendstr
            if os.path.isdir("/tmp/run/irc3"):
                subprocess.call(cmd, shell=True)

        return self.render_to_response(self.get_context_data(form=form))


def get_post(start_at, end_at, keyword=''):
    results = Log.objects.filter(created_at__range=(start_at, end_at)
                                 ).filter(message__contains=keyword).order_by('created_at')
    log_list = []
    for result in results:
        url_pat = r"https?://[a-zA-Z0-9\-./?@&=:~_#]+"
        message = result.message
        match_url = re.match(url_pat, message)
        if match_url:
            find = re.finditer(url_pat, message)
            for f in find:
                url = message[f.start():f.end()]
                message = message[:f.start()] + '<a href="' + url + '">' + url + '</a>' + message[f.end():]
        if result.attached_image:
            pass # TODO: attached_image
        else:
            log = {'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                   'command': result.command,
                   'message': message,
                   'channel': result.channel.id,
                   'nick': result.nick}
            log_list.append(log)
    return log_list


# SearchLogForm
def api_v1_search(request):
    if request.is_ajax():
        if request.method == 'GET':
            start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M:%S')
            end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M:%S')
            keyword = request.GET['keyword']
            log_list = get_post(start_at, end_at, keyword)

            channel_id_list = [c.id for c in Channel.objects.all()]
            return JsonResponse({'log_list': log_list, 'channel_id_list': channel_id_list})


def api_v1_now(request):
    if request.is_ajax():
        if request.method == 'GET':
            start_at = timezone.now() - datetime.timedelta(hours=3)
            end_at = timezone.now()
            log_list = get_post(start_at, end_at)

            channel_id_list = [c.id for c in Channel.objects.all()]
            return JsonResponse({'log_list': log_list, 'channel_id_list': channel_id_list})


def api_v1_next(request):
    if request.is_ajax():
        if request.method == 'GET':
            start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M:%S')
            end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M:%S')

            duration = end_at - start_at
            end_at += duration
            start_at += duration
            log_list = get_post(start_at, end_at)

            channel_id_list = [c.id for c in Channel.objects.all()]
            return JsonResponse({'log_list': log_list, 'channel_id_list': channel_id_list})


def api_v1_previous(request):
    if request.is_ajax():
        if request.method == 'GET':
            start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M:%S')
            end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M:%S')

            duration = end_at - start_at
            end_at -= duration
            start_at -= duration
            log_list = get_post(start_at, end_at)

            channel_id_list = [c.id for c in Channel.objects.all()]
            return JsonResponse({'log_list': log_list, 'channel_id_list': channel_id_list})
