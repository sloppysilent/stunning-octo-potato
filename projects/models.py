from django.conf import settings
from django.db import models

STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_CHOICES = [
    (STATUS_OPEN, "Open"),
    (STATUS_CLOSED, "Closed"),
]


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = models.URLField(blank=True)
    status = models.CharField(max_length=6, choices=STATUS_CHOICES, default="open")
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="participated_projects"
    )
    favorited_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="favorite_projects",
        through="Favorite",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "project"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.project}"
