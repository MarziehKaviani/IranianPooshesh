from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

import redis
from authentication.models import User
from core import variables
from base.serializers import *
from redis_service.utils import RedisStore, check_redis_health


class UserSerializer(ModelSerializerWithVerboseNames):
    """
    Serializer for User model.

    Attributes:
    ----------
    * `Meta`: ``class``
        Configuration class for the serializer.

        - `model`: ``User``
            The User model.
        - `fields`: ``list``
            List of fields to include in the serialized representation.
    """
    class Meta:
        model = User
        fields = [
            variables.PHONE_NUMBER,
        ]


class LoginSerializer(SerializerWithVerboseNames):
    """
    Serializer for user login.

    This serializer handles the validation of phone number and country code.
    It also provides methods to manage users and translates field names
    dynamically for the JSON response.
    """
    phone_number = serializers.CharField(max_length=18)
    country_code = serializers.CharField(max_length=7)
    verification_code = serializers.CharField(max_length=6)

    TRANSLATED_FIELD_NAMES = {
        variables.PHONE_NUMBER: _(variables.PHONE_NUMBER_VERBOSE_NAME),
        variables.COUNTRY_CODE: _(variables.COUNTRY_CODE_VERBOSE_NAME),
        variables.VERIFICATION_CODE: _(variables.VERIFICATION_CODE_VERBOSE_NAME),
    }

    def to_representation(self, instance):
        """
        Override to_representation to include translated field names in the JSON response dynamically.

        Parameters
        ----------
        instance : User
            The user instance to represent.

        Returns
        -------
        dict
            The JSON representation of the instance with translated field names.
        """
        ret = super().to_representation(instance)
        translated_fields = {}

        for field_name, field_value in ret.items():
            translated_name = self.TRANSLATED_FIELD_NAMES.get(
                field_name, field_name)
            translated_fields[translated_name] = field_value
        return translated_fields

    def validate(self, attrs):
        """
        Validate the input data.

        This method validates the country code and verification code to ensure they contain only digits.

        Parameters
        ----------
        attrs : dict
            The input data to validate.

        Returns
        -------
        dict
            The validated input data.

        Raises
        ------
        serializers.ValidationError
            If the country code or verification code is invalid.
        """
        if not attrs[variables.COUNTRY_CODE].isdigit():
            raise serializers.ValidationError(
                {variables.ERROR: INVALID_COUNTRY_CODE},
            )
        if not attrs[variables.VERIFICATION_CODE].isdigit():
            raise serializers.ValidationError(
                {variables.ERROR: f"{INVALID_INPUT_DATA}: {variables.VERIFICATION_CODE}"},
            )
        return super().validate(attrs)

    def user_exists(self, phone_number) -> bool:
        """
        Check if a user exists with the given phone number.

        Parameters
        ----------
        phone_number : str
            The phone number to check.

        Returns
        -------
        bool
            True if the user exists, False otherwise.
        """
        return User.objects.filter(phone_number=phone_number).first()

    def set_state(self, user, state):
        """
        Set the state of the user.

        Parameters
        ----------
        user : User
            The user object.
        state : str
            The new state value.

        Returns
        -------
        User
            The updated user object.
        """
        user.state = state
        user.save()
        return user


class SignUpSerializer(SerializerWithVerboseNames):

    phone_number = serializers.CharField(max_length=18)
    country_code = serializers.CharField(max_length=7)

    def user_exists(self, phone_number) -> None | User:
        """
        Check if a user exists with the given phone number.

        Parameters
        ----------
        phone_number : str
            The phone number to check.

        Returns
        -------
        User or None
            The user object if found, otherwise None.
        """
        return User.objects.filter(phone_number=phone_number).first()

    def get_user(self, phone_number):
        """
        Retrieve a user by phone number.

        Parameters
        ----------
        phone_number : str
            The phone number of the user to retrieve.

        Returns
        -------
        User
            The user object.
        """
        return User.objects.get(phone_number=phone_number)

    def create_user(self, phone_number):
        """
        Create a new user with the given phone number.

        Parameters
        ----------
        phone_number : str
            The phone number for the new user.

        Returns
        -------
        User
            The newly created user object.
        """
        user = User.objects.create(
            phone_number=phone_number, state=variables.PENDING)
        return user

    def change_state(self, user, value):
        """
        Change the state of the user.

        Parameters
        ----------
        user : User
            The user object.
        value : str
            The new state value.
        """
        user.state = value

    def validate(self, attrs):
        """
        Validate the input data.

        This method validates the country code to ensure it contains only digits.

        Parameters
        ----------
        attrs : dict
            The input data to validate.

        Returns
        -------
        dict
            The validated input data.

        Raises
        ------
        serializers.ValidationError
            If the country code is invalid.
        """
        if not attrs[variables.COUNTRY_CODE].isdigit():
            raise serializers.ValidationError(
                {variables.ERROR: INVALID_COUNTRY_CODE},
            )
        return super().validate(attrs)


class ProfileSerializer(ModelSerializerWithVerboseNames):
    """
    Serializer for Profile model.

    Attributes:
    ----------
    * `Meta`: ``class``
        Configuration class for the serializer.

        - `model`: ``Profile``
            The Profile model.
        - `fields`: ``str`` or ``list``
            The fields to include in the serialized representation.
    """
    class Meta:
        model = Profile
        fields = '__all__'


class UserVerificationSerializer(SerializerWithVerboseNames):
    """
    Serializer for user verification.

    This serializer handles the validation of user verification data including national code, birth date,
    phone number, and country code. It also provides methods to manage personal information in Redis.
    """
    national_code = serializers.CharField(required=True, max_length=10)
    birth_date = serializers.DateField(required=True)
    phone_number = serializers.CharField(max_length=18)
    country_code = serializers.CharField(required=True, max_length=7)

    # TODO Rename to more conceptual name
    def add_preview_to_redis(self, personal_info, user, count, national_code):
        """
        Add personal information preview to Redis.

        This method stores the personal information preview in Redis with a specified expiration time.

        Parameters
        ----------
        personal_info : dict
            The personal information data to store.
        user : User
            The user object.
        count : int
            The count of attempts or some relevant metric.
        national_code : str
            The national code of the user.
        """
        RedisStore().set(
            f"{variables.PERSONAL_INFO}:{user.pk}",
            {
                variables.PERSONAL_INFO: personal_info,
                variables.PHONE_NUMBER: user.phone_number,
                variables.COUNT: count,
                variables.IDENTITY_NUMBER: national_code
            },
            24 * 60 * 60
        )

    def get_personal_info(self, user):
        """
        Get personal information from Redis.

        This method retrieves and then removes the personal information stored in Redis for the given user.

        Parameters
        ----------
        user : User
            The user object.

        Returns
        -------
        dict or None
            The personal information retrieved from Redis, or None if not found.
        """
        return RedisStore().get(f"{variables.PERSONAL_INFO}:{user.pk}")


class PersonalInfoConfirmationSerializer(SerializerWithVerboseNames):
    """
    Serializer for confirming personal information.

    This serializer handles the validation of confirmation tokens and provides methods to update user profiles
    with verified data.
    """
    confirmation_token = serializers.CharField(required=True, max_length=10)

    def update_profile(self, user, data):
        """
        Update the user profile with verified information.

        This method updates the user profile with the provided data after successful verification.

        Parameters
        ----------
        user : User
            The user object.
        data : dict
            The verified personal information data.
        """
        profile = Profile.objects.get(user=user.pk, )
        print(data[PERSONAL_INFO], 4444444444)
        print('-----------------')
        print(data)
        profile.name = data[PERSONAL_INFO][FIRST_NAME]
        profile.last_name = data[PERSONAL_INFO][LAST_NAME]
        profile.identity_number = data[IDENTITY_NUMBER]
        profile.save()

    def get_user_preview_data(self, user):
        """
        Get the user preview data from Redis.

        This method retrieves the preview data stored in Redis for the given user.

        Parameters
        ----------
        user : User
            The user object.

        Returns
        -------
        dict or None
            The preview data retrieved from Redis, or None if not found.
        """
        return RedisStore().get(f"{variables.PERSONAL_INFO}:{user.pk}")

    def show_preview(self, user):
        prev = RedisStore().get(f"{variables.PERSONAL_INFO}:{user.pk}")
        return prev[variables.PERSONAL_INFO] if prev else None