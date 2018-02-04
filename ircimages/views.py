from django.views.generic import ListView

from .models import Image


# Create your views here.
class ImageListView(ListView):
    template_name = 'ircimages/index.html'
    model = Image
    context_object_name = 'image_list'
    paginate_by = 50

    class Meta:
        ordering = ['id']
