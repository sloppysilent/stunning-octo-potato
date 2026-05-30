import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    """Форма регистрации пользователя."""

    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    class Meta:
        model = User
        fields = ["name", "surname", "email"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """Форма входа в систему."""

    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")


class UserEditForm(forms.ModelForm):
    """Форма редактирования профиля."""

    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return phone

        pattern = re.compile(r"^(\+7|8)\d{10}$")
        if not pattern.match(phone):
            raise ValidationError(
                "Номер телефона должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
            )

        qs = User.objects.filter(phone=phone)
        if self.instance and qs.exclude(pk=self.instance.pk).exists():
            raise ValidationError("Этот номер телефона уже зарегистрирован")
        elif not self.instance and qs.exists():
            raise ValidationError("Этот номер телефона уже зарегистрирован")

        return phone

    def clean_github_url(self):
        github_url = self.cleaned_data.get("github_url", "").strip()
        if not github_url:
            return github_url

        try:
            validator = URLValidator()
            validator(github_url)
        except ValidationError:
            raise ValidationError("Введите корректную ссылку")

        if "github.com" not in github_url:
            raise ValidationError("Ссылка должна вести на GitHub")

        return github_url


class ChangePasswordForm(forms.Form):
    """Форма смены пароля."""

    old_password = forms.CharField(widget=forms.PasswordInput, label="Текущий пароль")
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="Новый пароль")
    new_password2 = forms.CharField(
        widget=forms.PasswordInput, label="Повторите новый пароль"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Неверный текущий пароль")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Пароли не совпадают")

        if new_password1:
            try:
                validate_password(new_password1, self.user)
            except ValidationError as e:
                self.add_error("new_password1", e)

        return cleaned_data

    def save(self):
        new_password = self.cleaned_data["new_password1"]
        self.user.set_password(new_password)
        self.user.save()

    def _generate_avatar(self, user):
        import io
        import random

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image, ImageDraw, ImageFont

        if user.name:
            colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
            img = Image.new("RGB", (200, 200), color=random.choice(colors))
            draw = ImageDraw.Draw(img)

            initial = user.name[0].upper()

            try:
                font = ImageFont.truetype("arial.ttf", 100)
            except Exception:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), initial, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((200 - text_width) // 2, (200 - text_height) // 2)

            draw.text(position, initial, fill="white", font=font)

            img_io = io.BytesIO()
            img.save(img_io, format="PNG")
            img_io.seek(0)

            filename = f"avatar_{user.id}_{user.email}.png"
            user.avatar.save(
                filename, SimpleUploadedFile(filename, img_io.read()), save=True
            )
