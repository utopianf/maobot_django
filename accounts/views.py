from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render

from .forms import IrcUserCreationForm

# Create your views here.
@login_required
def index(request):
    return render(request, 'accounts/index.html')

def new(request):
    form = IrcUserCreationForm()
    return render(request, 'accounts/new.html', {'form': form,})

def create(request):
    if request.method == 'POST':
        form = IrcUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('./login')
        return render(request, 'accounts/new.html', {'form': form,})
    else:
        raise Http404
