from django.contrib import admin
from django.urls import path

from . import views

app_name = 'ircimages'
admin.AdminSite.site_header = app_name + ' Administration'
urlpatterns = [
    path('', views.ImageListView.as_view(), name='index'),
]
