from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

        labels = {
            'username': 'Customer Name',
            'password1': 'Password',
            'password2': 'Confirm Password',
        }

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your name'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data['username'].strip()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                'This customer name is already registered.'
            )

        return username