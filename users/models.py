# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager
from .utils import generate_user_avatar

SKILL_NAME_MAX_LENGTH = 124
USER_NAME_MAX_LENGTH = 124
USER_PHONE_MAX_LENGTH = 12
USER_ABOUT_MAX_LENGTH = 256


class Skill(models.Model):
    """Модель навыка."""

    name = models.CharField(max_length=SKILL_NAME_MAX_LENGTH, unique=True)

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Кастомная модель пользователя."""

    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    avatar = models.ImageField(
        upload_to="avatars/", blank=True, null=True
    )
    phone = models.CharField(max_length=USER_PHONE_MAX_LENGTH, blank=True)
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=USER_ABOUT_MAX_LENGTH, blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name="users")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    class Meta:
        ordering = ["-id"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.avatar and self.name:
            generate_user_avatar(self)
            super().save(update_fields=["avatar"])
