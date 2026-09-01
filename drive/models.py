import uuid

from django.contrib.auth.models import User
from django.db import models


class Folder(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="folders"
    )

    name = models.CharField(max_length=100)

    parent_folder = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subfolders"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CloudFile(models.Model):

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="files"
    )

    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="files"
    )

    file = models.FileField(upload_to="uploads/")

    original_name = models.CharField(max_length=255)

    file_size = models.PositiveBigIntegerField(default=0)

    file_type = models.CharField(max_length=50)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    is_favorite = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.original_name


class SharedFile(models.Model):

    PERMISSION_CHOICES = [
        ("viewer", "Viewer"),
        ("editor", "Editor"),
    ]

    file = models.ForeignKey(
        CloudFile,
        on_delete=models.CASCADE,
        related_name="shared_users"
    )

    shared_with = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    permission = models.CharField(
        max_length=10,
        choices=PERMISSION_CHOICES,
        default="viewer"
    )

    share_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.original_name} -> {self.shared_with.username}"
