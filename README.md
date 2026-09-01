# Cloud File Sharing System

A Django-based cloud drive project for user registration, login, folder organization, file upload, download, and basic deletion.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Current Features

- User registration, login, and logout
- Create folders and nested subfolders
- Rename and delete folders
- Upload files into the root drive or a folder
- Share files with another user as viewer or editor
- View files shared by other users in "Shared With Me"
- Download files owned by the signed-in user or shared with them
- Soft-delete files from the drive view
- Django admin configuration for folders, files, and sharing records

## Useful Commands

```powershell
python manage.py check
python manage.py test
```

## Suggested Next Features

- Trash/recovery page for soft-deleted files
- Storage quota per user
- Search and file type filters
- Public share links using `SharedFile.share_token`
- Production settings with environment variables
