from django.contrib import admin
from django.urls import path

from . import views

app_name = 'irclog'
admin.AdminSite.site_header = app_name + ' Administration'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('api/v1/post', views.api_v1_post, name='api_v1_post'),
    path('api/v1/search', views.api_v1_search, name='api_v1_search'),
    path('api/v1/next', views.api_v1_next, name='api_v1_next'),
    path('api/v1/now', views.api_v1_now, name='api_v1_now'),
    path('api/v1/previous', views.api_v1_previous, name='api_v1_previous'),
    path('api/v1/allchannels', views.api_v1_allchannels, name='api_v1_allchannels'),
]
