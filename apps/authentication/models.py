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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email}"
