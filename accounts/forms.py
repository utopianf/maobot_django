from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import IrcUser


class IrcUserCreationForm(UserCreationForm):

    passphrase = forms.CharField(max_length=10)

    class Meta:
        model = IrcUser
        fields = (
            'username', 'password1', 'password2', 'passphrase')

    def clean(self):
        cleaned_data = super(IrcUserCreationForm, self).clean()

        if cleaned_data.get('passphrase') != 'naokun':
            self.add_error('passphrase', 'Wrong passphrase')
