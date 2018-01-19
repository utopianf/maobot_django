from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class IrcUser(AbstractUser):
    email = models.EmailField('Email Address', blank=True, null=True)
