from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(_('Email Address'), max_length=191, unique=True)
    name = models.CharField(_('Full Name'), max_length=150)

    # Django-required flags
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Phase 1 additions
    storage_mode = models.CharField(
        max_length=10,
        choices=[('cloud', 'Cloud Storage'), ('file', 'File Storage')],
        default='cloud',
        help_text="User's data storage preference"
    )
    encryption_key_salt = models.CharField(
        max_length=255,
        blank=True,
        help_text="Salt for deriving encryption key in file mode"
    )
    preferred_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('cs', 'Czech')],
        default='en'
    )
    credit_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Available credits for paid features"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email}"
