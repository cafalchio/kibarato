import getpass
import os
import secrets
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create a staff login limited to viewing, adding, editing and deleting promotions."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--password-file", help="Generate a password and save it to a NEW private file instead of prompting.")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        if User.objects.filter(username=username).exists():
            raise CommandError("Username already exists; no existing account was changed.")
        user = User(username=username, is_staff=True, is_superuser=False, is_active=True)
        destination = options["password_file"]
        if destination:
            password = secrets.token_urlsafe(24)
        else:
            password = getpass.getpass("Password: ")
            if password != getpass.getpass("Password (again): "):
                raise CommandError("Passwords do not match.")
        try:
            validate_password(password, user)
            user.full_clean(exclude=["password"])
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        permissions = Permission.objects.filter(
            content_type__app_label="promotions", content_type__model="promotion",
            codename__in=["view_promotion", "add_promotion", "change_promotion", "delete_promotion"],
        )
        if permissions.count() != 4:
            raise CommandError("Run migrate before creating the account.")
        with transaction.atomic():
            user.set_password(password)
            user.save()
            user.user_permissions.set(permissions)
            if destination:
                try:
                    fd = os.open(Path(destination), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(fd, "w") as file:
                        file.write(f"Username: {username}\nPassword: {password}\n")
                except OSError as exc:
                    raise CommandError("Could not create password file; account creation rolled back.") from exc
        self.stdout.write(self.style.SUCCESS(f"Created promotions-only staff account: {username}"))
