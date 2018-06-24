from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import JsonResponse

from .models import Image


# Create your views here.
class ImageListView(LoginRequiredMixin, ListView):
    template_name = 'ircimages/index.html'
    model = Image

    login_url = 'accounts:login'
    redirect_field_name = 'redirect_to'

    context_object_name = 'image_list'
    paginate_by = 50


def get_images(start_at, end_at, keyword=''):
    results = Image.objects.filter(created_at__range=(start_at, end_at + datetime.timedelta(minutes=1))
            ).filter(caption__contains=keyword).order_by('created_at')


def api_v1_getallimages(request):
    images = Image.objects.all()
    return JsonResponse({'images': images})



