from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Ism", max_length=100)
    last_name = forms.CharField(label="Familiya", max_length=100)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "password1", "password2"]
        labels = {"username": "Login (lotin harflarida)"}


class EnrollRequestForm(forms.Form):
    phone = forms.CharField(
        label="Telefon raqami",
        max_length=30,
        help_text="To'lovni tasdiqlash uchun shu raqamga bog'lanamiz.",
    )
    note = forms.CharField(
        label="Izoh (ixtiyoriy)",
        max_length=300,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
