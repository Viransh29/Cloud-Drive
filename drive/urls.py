from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("folder/<int:folder_id>/", views.folder_detail, name="folder_detail"),
    path(
        "folder/<int:folder_id>/rename/",
        views.rename_folder,
        name="rename_folder"
    ),
    path(
        "folder/<int:folder_id>/delete/",
        views.delete_folder,
        name="delete_folder"
    ),
    path(
        "file/<int:file_id>/download/",
        views.download_file,
        name="download_file"
    ),
    path(
        "file/<int:file_id>/share/",
        views.share_file,
        name="share_file"
    ),
    path(
        "file/<int:file_id>/delete/",
        views.delete_file,
        name="delete_file"
    ),
    path(
        "share/<int:share_id>/remove/",
        views.unshare_file,
        name="unshare_file"
    ),
    path(
        "shared-with-me/",
        views.shared_with_me,
        name="shared_with_me"
    ),
]
