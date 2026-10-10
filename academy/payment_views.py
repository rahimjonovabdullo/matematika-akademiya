import re

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from .models import PaymentSettings


def _is_staff(user):
    return user.is_authenticated and user.is_staff


class PaymentSettingsForm(forms.ModelForm):
    class Meta:
        model = PaymentSettings
        fields = ["card_number", "card_owner", "bank_name", "telegram", "instructions"]
        widgets = {
            "card_number": forms.TextInput(attrs={"placeholder": "8600 1234 5678 9012", "inputmode": "numeric", "autocomplete": "off"}),
            "card_owner": forms.TextInput(attrs={"placeholder": "Ism Familiya"}),
            "bank_name": forms.TextInput(attrs={"placeholder": "Masalan: Uzcard / Humo / Xalq banki"}),
            "telegram": forms.TextInput(attrs={"placeholder": "@sizning_telegram"}),
            "instructions": forms.Textarea(attrs={"rows": 3, "placeholder": "Masalan: To'lov izohiga ismingizni yozing."}),
        }

    def clean_card_number(self):
        raw = self.cleaned_data.get("card_number", "")
        digits = re.sub(r"\D", "", raw)
        if not digits:
            return ""
        if len(digits) != 16:
            raise forms.ValidationError("Karta raqami 16 ta raqamdan iborat bo'lishi kerak.")
        return " ".join(digits[i:i + 4] for i in range(0, 16, 4))

    def clean_telegram(self):
        t = self.cleaned_data.get("telegram", "").strip()
        if not t:
            return ""
        h = t
        for p in ("https://t.me/", "http://t.me/", "t.me/", "@"):
            if h.lower().startswith(p):
                h = h[len(p):]
        h = h.strip("/ ")
        if not re.fullmatch(r"[A-Za-z0-9_]{4,32}", h):
            raise forms.ValidationError("Telegram manzili noto'g'ri. Masalan: @sizning_telegram")
        return "@" + h


@login_required
@user_passes_test(_is_staff)
def manage_payment_settings(request):
    obj = PaymentSettings.load()
    if request.method == "POST":
        form = PaymentSettingsForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "To'lov sozlamalari saqlandi.")
            return redirect("manage_payment")
    else:
        form = PaymentSettingsForm(instance=obj)
    return render(request, "academy/manage/payment_settings.html", {"form": form, "ready": obj.is_ready})
