from django.contrib import admin

from .models import CloudFile, Folder, SharedFile


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "parent_folder", "created_at")
    search_fields = ("name", "user__username")
    list_filter = ("created_at",)


@admin.register(CloudFile)
class CloudFileAdmin(admin.ModelAdmin):
    list_display = (
        "original_name",
        "owner",
        "folder",
        "file_size",
        "file_type",
        "uploaded_at",
        "is_deleted",
    )
    search_fields = ("original_name", "owner__username")
    list_filter = ("is_deleted", "uploaded_at", "file_type")


@admin.register(SharedFile)
class SharedFileAdmin(admin.ModelAdmin):
    list_display = ("file", "shared_with", "permission", "created_at")
    search_fields = ("file__original_name", "shared_with__username")
    list_filter = ("permission", "created_at")
