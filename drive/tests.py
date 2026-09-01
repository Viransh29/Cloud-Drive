from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from tempfile import TemporaryDirectory

from .models import CloudFile, Folder, SharedFile


class DriveWorkflowTests(TestCase):

    def setUp(self):
        self.temp_media = TemporaryDirectory()
        self.override_media = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.override_media.enable()
        self.user = User.objects.create_user(
            username="testuser",
            password="strong-pass-123"
        )
        self.other_user = User.objects.create_user(
            username="shareduser",
            password="strong-pass-123"
        )

    def tearDown(self):
        self.override_media.disable()
        self.temp_media.cleanup()

    def test_authenticated_user_can_create_folder(self):
        self.client.login(username="testuser", password="strong-pass-123")

        response = self.client.post(
            reverse("dashboard"),
            {
                "action": "create_folder",
                "name": "Projects",
            }
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(
            Folder.objects.filter(user=self.user, name="Projects").exists()
        )

    def test_folder_names_are_unique_per_parent(self):
        Folder.objects.create(user=self.user, name="Projects")
        self.client.login(username="testuser", password="strong-pass-123")

        response = self.client.post(
            reverse("dashboard"),
            {
                "action": "create_folder",
                "name": "projects",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Folder with this name already exists.")
        self.assertEqual(Folder.objects.filter(user=self.user).count(), 1)

    def test_authenticated_user_can_upload_file(self):
        self.client.login(username="testuser", password="strong-pass-123")
        uploaded_file = SimpleUploadedFile(
            "notes.txt",
            b"hello cloud",
            content_type="text/plain"
        )

        response = self.client.post(
            reverse("dashboard"),
            {
                "action": "upload_file",
                "file": uploaded_file,
            }
        )

        self.assertRedirects(response, reverse("dashboard"))
        cloud_file = CloudFile.objects.get(owner=self.user)
        self.assertEqual(cloud_file.original_name, "notes.txt")
        self.assertEqual(cloud_file.file_size, 11)

    def test_user_cannot_view_another_users_folder(self):
        folder_owner = User.objects.create_user(
            username="other",
            password="strong-pass-123"
        )
        folder = Folder.objects.create(user=folder_owner, name="Private")
        self.client.login(username="testuser", password="strong-pass-123")

        response = self.client.get(
            reverse("folder_detail", args=[folder.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_share_file_with_another_user(self):
        cloud_file = self.create_cloud_file()
        self.client.login(username="testuser", password="strong-pass-123")

        response = self.client.post(
            reverse("share_file", args=[cloud_file.id]),
            {
                "username": "shareduser",
                "permission": "viewer",
            }
        )

        self.assertRedirects(
            response,
            reverse("share_file", args=[cloud_file.id])
        )
        self.assertTrue(
            SharedFile.objects.filter(
                file=cloud_file,
                shared_with=self.other_user,
                permission="viewer"
            ).exists()
        )

    def test_shared_user_can_download_shared_file(self):
        cloud_file = self.create_cloud_file()
        SharedFile.objects.create(
            file=cloud_file,
            shared_with=self.other_user,
            permission="viewer"
        )
        self.client.login(username="shareduser", password="strong-pass-123")

        response = self.client.get(
            reverse("download_file", args=[cloud_file.id])
        )

        self.assertEqual(response.status_code, 200)
        response.close()

    def test_unshared_user_cannot_download_private_file(self):
        cloud_file = self.create_cloud_file()
        self.client.login(username="shareduser", password="strong-pass-123")

        response = self.client.get(
            reverse("download_file", args=[cloud_file.id])
        )

        self.assertEqual(response.status_code, 404)

    def create_cloud_file(self):
        uploaded_file = SimpleUploadedFile(
            "shared.txt",
            b"shared cloud file",
            content_type="text/plain"
        )

        return CloudFile.objects.create(
            owner=self.user,
            file=uploaded_file,
            original_name="shared.txt",
            file_size=17,
            file_type="text/plain"
        )
