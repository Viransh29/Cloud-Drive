from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    FileUploadForm,
    FolderForm,
    LoginForm,
    RegisterForm,
    ShareFileForm,
)
from .models import CloudFile, Folder, SharedFile


def home(request):
    return render(request, "home.html")


def register_view(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()
            login(request, user)
            return redirect("dashboard")

    else:

        form = RegisterForm()

    return render(
        request,
        "authentication/register.html",
        {
            "form": form
        }
    )


def login_view(request):

    if request.method == "POST":

        form = LoginForm(request, data=request.POST)

        if form.is_valid():

            user = form.get_user()
            login(request, user)
            return redirect("dashboard")

    else:

        form = LoginForm()

    return render(
        request,
        "authentication/login.html",
        {
            "form": form
        }
    )


@login_required
def dashboard_view(request):
    return _drive_view(request, current_folder=None)


@login_required
def folder_detail(request, folder_id):

    current_folder = get_object_or_404(
        Folder,
        id=folder_id,
        user=request.user
    )

    return _drive_view(request, current_folder=current_folder)


def _drive_view(request, current_folder):

    folder_form = FolderForm(
        user=request.user,
        parent_folder=current_folder
    )
    upload_form = FileUploadForm()

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "create_folder":

            folder_form = FolderForm(
                request.POST,
                user=request.user,
                parent_folder=current_folder
            )

            if folder_form.is_valid():
                folder = folder_form.save(commit=False)
                folder.user = request.user
                folder.parent_folder = current_folder
                folder.save()

                messages.success(request, "Folder created successfully.")
                return redirect_current_folder(current_folder)

        elif action == "upload_file":

            upload_form = FileUploadForm(request.POST, request.FILES)

            if upload_form.is_valid():
                uploaded_file = upload_form.cleaned_data["file"]
                cloud_file = upload_form.save(commit=False)
                cloud_file.owner = request.user
                cloud_file.folder = current_folder
                cloud_file.original_name = uploaded_file.name
                cloud_file.file_size = uploaded_file.size
                cloud_file.file_type = uploaded_file.content_type or "unknown"
                cloud_file.save()

                messages.success(request, "File uploaded successfully.")
                return redirect_current_folder(current_folder)

    folders = Folder.objects.filter(
        user=request.user,
        parent_folder=current_folder
    ).order_by("name")

    files = CloudFile.objects.filter(
        owner=request.user,
        folder=current_folder,
        is_deleted=False
    ).order_by("-uploaded_at")

    context = {
        "current_folder": current_folder,
        "breadcrumbs": get_breadcrumbs(current_folder),
        "folders": folders,
        "files": files,
        "folder_form": folder_form,
        "upload_form": upload_form,
        "form": folder_form,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )


@login_required
def rename_folder(request, folder_id):

    folder = get_object_or_404(
        Folder,
        id=folder_id,
        user=request.user
    )

    if request.method == "POST":

        form = FolderForm(
            request.POST,
            instance=folder,
            user=request.user,
            parent_folder=folder.parent_folder,
            current_folder=folder
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Folder renamed successfully.")
            return redirect_current_folder(folder.parent_folder)

    else:

        form = FolderForm(
            instance=folder,
            user=request.user,
            parent_folder=folder.parent_folder,
            current_folder=folder
        )

    return render(
        request,
        "dashboard/rename_folder.html",
        {
            "form": form,
            "folder": folder
        }
    )


@login_required
def delete_folder(request, folder_id):

    folder = get_object_or_404(
        Folder,
        id=folder_id,
        user=request.user
    )
    parent_folder = folder.parent_folder

    if request.method == "POST":
        folder.delete()
        messages.success(request, "Folder deleted successfully.")

    return redirect_current_folder(parent_folder)


@login_required
def share_file(request, file_id):

    cloud_file = get_object_or_404(
        CloudFile,
        id=file_id,
        owner=request.user,
        is_deleted=False
    )

    if request.method == "POST":
        form = ShareFileForm(request.POST, owner=request.user)

        if form.is_valid():
            shared_file = SharedFile.objects.filter(
                file=cloud_file,
                shared_with=form.shared_with
            ).first()

            if shared_file:
                shared_file.permission = form.cleaned_data["permission"]
                shared_file.save(update_fields=["permission"])
                messages.success(request, "Sharing permission updated.")
            else:
                SharedFile.objects.create(
                    file=cloud_file,
                    shared_with=form.shared_with,
                    permission=form.cleaned_data["permission"]
                )
                messages.success(request, "File shared successfully.")

            return redirect("share_file", file_id=cloud_file.id)

    else:
        form = ShareFileForm(owner=request.user)

    shared_users = SharedFile.objects.filter(
        file=cloud_file
    ).select_related("shared_with").order_by("shared_with__username")

    return render(
        request,
        "dashboard/share_file.html",
        {
            "form": form,
            "file": cloud_file,
            "shared_users": shared_users,
        }
    )


@login_required
def unshare_file(request, share_id):

    shared_file = get_object_or_404(
        SharedFile,
        id=share_id,
        file__owner=request.user
    )
    file_id = shared_file.file.id

    if request.method == "POST":
        shared_file.delete()
        messages.success(request, "File access removed.")

    return redirect("share_file", file_id=file_id)


@login_required
def shared_with_me(request):

    shared_files = SharedFile.objects.filter(
        shared_with=request.user,
        file__is_deleted=False
    ).select_related("file", "file__owner").order_by("-created_at")

    return render(
        request,
        "dashboard/shared_with_me.html",
        {
            "shared_files": shared_files
        }
    )


@login_required
def download_file(request, file_id):

    cloud_file = get_accessible_file(file_id, request.user)

    return FileResponse(
        cloud_file.file.open("rb"),
        as_attachment=True,
        filename=cloud_file.original_name
    )


@login_required
def delete_file(request, file_id):

    cloud_file = get_object_or_404(
        CloudFile,
        id=file_id,
        owner=request.user,
        is_deleted=False
    )
    current_folder = cloud_file.folder

    if request.method == "POST":
        cloud_file.is_deleted = True
        cloud_file.save(update_fields=["is_deleted"])
        messages.success(request, "File removed from your drive.")

    return redirect_current_folder(current_folder)


def logout_view(request):

    logout(request)
    return redirect("home")


def get_accessible_file(file_id, user):

    cloud_file = get_object_or_404(
        CloudFile,
        id=file_id,
        is_deleted=False
    )

    if cloud_file.owner_id == user.id:
        return cloud_file

    if SharedFile.objects.filter(file=cloud_file, shared_with=user).exists():
        return cloud_file

    raise Http404("File not found.")


def redirect_current_folder(folder):

    if folder:
        return redirect("folder_detail", folder_id=folder.id)

    return redirect("dashboard")


def get_breadcrumbs(folder):

    breadcrumbs = []
    current = folder

    while current:
        breadcrumbs.append(current)
        current = current.parent_folder

    return list(reversed(breadcrumbs))
