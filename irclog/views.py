import datetime
from datetime import datetime as dt
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import CreateView

from .forms import LogCreateForm
from .models import Channel, Log


# Create your views here.
class IndexView(LoginRequiredMixin, CreateView):
    """
    path: /irclog/
    Just an index.
    """
    template_name = 'irclog/index.html'
    model = Log
    form_class = LogCreateForm

    login_url = 'accounts:login'
    redirect_field_name = 'redirect_to'

    def get_context_data(self, **kwargs):
        # Make context
        context = super(IndexView, self).get_context_data(**kwargs)
        context['current_user'] = self.request.user
        return context


def api_v1_allchannels(request):
    """
    Returns joined channel lists.
    """
    channels = Channel.objects.all()
    channel_list = []
    for c in channels:
        channel = {'id': c.id,
                   'name': c.name,
                   'members': c.ircusers,
                   'topic': c.topic,}
        channel_list.append(channel)
    return JsonResponse({'channels': channel_list})


def get_irclog_info(start_at, end_at, keyword=''):
    """
    Returns irclog information.
    :param start_at: find log from the time
    :param end_at: find log till the time
    :param keyword: find log with the keyword
    :return: a dict including a log list
    """
    results = Log.objects.filter(created_at__range=(start_at, end_at + datetime.timedelta(minutes=1))
                                 ).filter(message__contains=keyword).order_by('created_at')
    log_list = []
    for result in results:
        url_pat = r"https?://[a-zA-Z0-9\-./?@&=:~_#]+"
        message = result.message
        match_url = re.search(url_pat, message)
        if match_url:
            find = re.finditer(url_pat, message)
            for f in find:
                url = message[f.start():f.end()]
                message = message[:f.start()] + '<a href="' + url + '">' + url + '</a>' + message[f.end():]
        log = {'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S'),
               'command': result.command,
               'message': message,
               'channel': result.channel.id,
               'nick': result.nick,
               'is_from_log': result.is_from_log,
               }
        if result.attached_image:
            log['attached_image_url'] = result.attached_image.url
        log_list.append(log)
    irclog_info = {
        'log_list': log_list,
        'start_at': start_at.strftime('%Y-%m-%dT%H:%M'),
        'end_at': end_at.strftime('%Y-%m-%dT%H:%M'),
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
        create_form = LogCreateForm(request.POST)
        if create_form.is_valid():
            create_form.save()
            return JsonResponse({'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                                 'end_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
                                 'message': create_form.cleaned_data.get('message'),
                                 'channel': create_form.cleaned_data.get('channel').id})


# SearchLogForm
def api_v1_search(request):
    """
    API when pressing search
    :param request:
    :return:
    """
    if request.is_ajax() and request.method == 'GET':
        start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M')
        end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M')
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
        start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M')
        end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M')

        duration = end_at - start_at
        end_at += duration
        start_at += duration

        irclog_info = get_irclog_info(start_at, end_at)
        return JsonResponse(irclog_info)


def api_v1_previous(request):
    if request.is_ajax() and request.method == 'GET':
        start_at = dt.strptime(request.GET['start_at'], '%Y-%m-%dT%H:%M')
        end_at = dt.strptime(request.GET['end_at'], '%Y-%m-%dT%H:%M')

        duration = end_at - start_at
        end_at -= duration
        start_at -= duration

        irclog_info = get_irclog_info(start_at, end_at)
        return JsonResponse(irclog_info)
