import datetime
from datetime import datetime as dt
import os
import subprocess
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import ListView

from .forms import LogCreateForm
from .models import Channel, Log


# Create your views here.
class IndexView(LoginRequiredMixin, ListView):
    """
    path: /irclog/
    Just an index.
    """
    template_name = 'irclog/index.html'
    model = Log

    login_url = 'accounts:login'
    redirect_field_name = 'redirect_to'

    def get_context_data(self, **kwargs):
        # init setting
        end_at = timezone.now()
        start_at = timezone.now() - datetime.timedelta(hours=3)
        channel = Channel.objects.all()[0]

        qs = Log.objects.filter(created_at__range=(start_at, end_at)).order_by('created_at')

        # Make context
        context = super(IndexView, self).get_context_data(**kwargs)
        context['log_list'] = qs
        context['channel'] = channel
        context['end_at'] = end_at.strftime('%Y-%m-%dT%H:%M:%S')
        context['start_at'] = start_at.strftime('%Y-%m-%dT%H:%M:%S')
        context['channels'] = Channel.objects.all()
        context['current_user'] = self.request.user
        return context


def get_irclog_info(start_at, end_at, keyword=''):
    """
    Returns irclog information.
    :param start_at: find log from the time
    :param end_at: find log till the time
    :param keyword: find log with the keyword
    :return: a dict including a log list
    """
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
            pass  # TODO: handle with attached_image
        else:
            log = {'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                   'command': result.command,
                   'message': message,
                   'channel': result.channel.id,
                   'nick': result.nick}
            log_list.append(log)
    irclog_info = {
        'log_list': log_list,
        'start_at': start_at.strftime('%Y-%m-%dT%H:%M:%S'),
        'end_at': end_at.strftime('%Y-%m-%dT%H:%M:%S'),
        'channel_id_list': [c.id for c in Channel.objects.all()]
    }
    return irclog_info


# CreateLogForm
def api_v1_post(request):
    """
    API to post a log
    :param request:
    :return:
    """
    if request.is_ajax() and request.method == 'POST':
        print(request.POST)
        create_form = LogCreateForm(request.POST)
        print(create_form.errors)
        if create_form.is_valid():
            create_form.save()
            return JsonResponse({'created_at': dt.now().strftime('%Y-%m-%d %H:%M:%S'),
                                 'end_at': dt.now().strftime('%Y-%m-%dT%H:%M:%S'),
                                 'message': create_form.cleaned_data.get('message')})


# SearchLogForm
def api_v1_search(request):
    """
    API when pressing search
    :param request:
    :return:
    """
    if request.is_ajax() and request.method == 'GET':
        start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M:%S')
        end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M:%S')
        keyword = request.GET['keyword']

        irclog_info = get_irclog_info(start_at, end_at, keyword)
        return JsonResponse(irclog_info)


def api_v1_now(request):
    """
    API when pressing now
    :param request:
    :return: log list
    """
    if request.is_ajax() and request.method == 'GET':
        start_at = timezone.now() - datetime.timedelta(hours=3)
        end_at = timezone.now()

        irclog_info = get_irclog_info(start_at, end_at)
        return JsonResponse(irclog_info)


def api_v1_next(request):
    if request.is_ajax() and request.method == 'GET':
        start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M:%S')
        end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M:%S')

        duration = end_at - start_at
        end_at += duration
        start_at += duration

        irclog_info = get_irclog_info(start_at, end_at)
        return JsonResponse(irclog_info)


def api_v1_previous(request):
    if request.is_ajax() and request.method == 'GET':
        start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M:%S')
        end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M:%S')

        duration = end_at - start_at
        end_at -= duration
        start_at -= duration

        irclog_info = get_irclog_info(start_at, end_at)
        return JsonResponse(irclog_info)
