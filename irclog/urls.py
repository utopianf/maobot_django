from django.contrib import admin
from django.urls import path

from . import views

app_name = 'irclog'
admin.AdminSite.site_header = app_name + ' Administration'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
]
