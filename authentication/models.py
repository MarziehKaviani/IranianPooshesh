from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, Group, Permission,
                                        PermissionsMixin)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from modeltranslation.decorators import register
from modeltranslation.translator import TranslationOptions

from .choices import *
from .manager import CustomUserManager
from core import variables


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the application.

    This model extends Django's AbstractBaseUser and PermissionsMixin to provide
    custom user fields and functionality.

    Attributes
    ----------
    phone_number : str
        Unique phone number of the user, serves as the username.
    state : str
        State of the user, with choices defined in USER_STATE.
    created_at : datetime
        Timestamp of when the user was created.
    is_active : bool
        Boolean indicating whether the user is active.
    is_staff : bool
        Boolean indicating whether the user is a staff member.
    objects : CustomUserManager
        Custom manager for the User model.

    Relationships
    -------------
    groups : ManyToManyField
        Groups the user belongs to, related to Django's Group model.
    user_permissions : ManyToManyField
        Permissions assigned to the user, related to Django's Permission model.

    Methods
    -------
    __str__():
        Returns the string representation of the user.
    """
    phone_number = models.CharField(
        # one for +, 7 for maximum len of country code and 10 for maximum national phone number len.
        max_length=18,
        unique=True,
        verbose_name=_(variables.PHONE_NUMBER_VERBOSE_NAME),
    )
    state = models.CharField(
        max_length=32, verbose_name=_(variables.STATE_VERBOSE_NAME), choices=variables.USER_STATE, null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_(variables.CREATED_AT_VERBOSE_NAME)
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField(
        Group, verbose_name=_("Groups"), blank=True, related_name="user_groups"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_(variables.USER_PERMISSIONS_VERBOSE_NAME),
        blank=True,
        related_name="user_permissions",
    )

    def __str__(self) -> str:
        return self.phone_number

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

