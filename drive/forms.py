from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import CloudFile, Folder, SharedFile


class RegisterForm(UserCreationForm):

    email = forms.EmailField()

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )


class LoginForm(AuthenticationForm):
    pass


class FolderForm(forms.ModelForm):

    class Meta:
        model = Folder
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Folder Name"
                }
            )
        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop("user", None)
        self.parent_folder = kwargs.pop("parent_folder", None)
        self.current_folder = kwargs.pop("current_folder", None)

        super().__init__(*args, **kwargs)

    def clean_name(self):

        name = self.cleaned_data["name"].strip()

        query = Folder.objects.filter(
            user=self.user,
            parent_folder=self.parent_folder,
            name__iexact=name
        )

        if self.current_folder:
            query = query.exclude(id=self.current_folder.id)

        if query.exists():
            raise forms.ValidationError(
                "Folder with this name already exists."
            )

        return name


class FileUploadForm(forms.ModelForm):

    class Meta:
        model = CloudFile
        fields = ["file"]

        widgets = {
            "file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            )
        }

    def clean_file(self):

        uploaded_file = self.cleaned_data["file"]
        max_size = 25 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise forms.ValidationError(
                "File size must be 25 MB or smaller."
            )

        return uploaded_file


class ShareFileForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username"
            }
        )
    )
    permission = forms.ChoiceField(
        choices=SharedFile.PERMISSION_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop("owner", None)
        self.shared_with = None
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise forms.ValidationError("No user found with this username.")

        if self.owner and user == self.owner:
            raise forms.ValidationError("You cannot share a file with yourself.")

        self.shared_with = user
        return username
