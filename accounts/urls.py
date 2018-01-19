from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts'
admin.AdminSite.site_header = app_name + ' Administration'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(
         template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
         template_name='accounts/logout.html'), name='logout'),
    path('new/', views.new, name='new'),
    path('create/', views.create, name='create'),
]
