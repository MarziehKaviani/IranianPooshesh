from django.contrib.auth.models import BaseUserManager

from common import variables
from common.variables import PHONE_NUMBER_REQUIRED


class CustomUserManager(BaseUserManager):
    """
    Custom manager for the User model to handle the creation of users and superusers.

    Methods
    -------
    create_user(phone_number, password=None, state=variables.PENDING, **extra_fields):
        Creates and saves a regular user with the given phone number and password.
    create_superuser(phone_number, password=None, state=variables.PENDING, **extra_fields):
        Creates and saves a superuser with the given phone number and password.
    """
    def create_user(self, phone_number, password=None, state=variables.PENDING, **extra_fields):
        """
        Create and return a regular user with the given phone number and password.

        Parameters
        ----------
        phone_number : str
            The phone number of the user.
        password : str, optional
            The password of the user (default is None).
        state : str, optional
            The state of the user (default is variables.PENDING).
        **extra_fields : dict
            Additional fields for the user.

        Returns
        -------
        user : User
            The created user instance.

        Raises
        ------
        ValueError
            If the phone number is not provided.
        """
        if not phone_number:
            raise ValueError(PHONE_NUMBER_REQUIRED)
        user = self.model(phone_number=phone_number,
                          state=state, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, state=variables.PENDING, **extra_fields):
        """
        Create and return a superuser with the given phone number and password.

        Parameters
        ----------
        phone_number : str
            The phone number of the superuser.
        password : str, optional
            The password of the superuser (default is None).
        state : str, optional
            The state of the superuser (default is variables.PENDING).
        **extra_fields : dict
            Additional fields for the superuser.

        Returns
        -------
        superuser : User
            The created superuser instance.

        Raises
        ------
        ValueError
            If is_staff is not set to True.
        ValueError
            If is_superuser is not set to True.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, state=state, **extra_fields)
