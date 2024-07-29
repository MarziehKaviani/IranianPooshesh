from django.contrib.auth.models import AnonymousUser
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.choices import *
from authentication.models import User
from authentication.permissions import AnonymousTokenPermission
from authentication.v1.serializers import (SignUpSerializer,
                                           LoginSerializer)
from authentication.v1.utils.otp import create_verification_code
from authentication.v1.utils.otp import load_otp_adapter_lazy as OTPAdapter
from authentication.v1.utils.token import generate_token
from authentication.v1.utils.utils import normilize_phone_number
from authentication.validators import (PhoneNumberValidatorAdapter,
                                       country_code_validator)
from common import variables
from common.utils import BaseResponse, BaseTime
from common.validators import check_api_input_data
from common.variables import *
from common.variables import BUSINESS_STATUS
from common.utils import countries_hints_dict


class SignUpViewSet(
    viewsets.GenericViewSet,
):
    permission_classes = [AnonymousTokenPermission]
    queryset = User.objects.all()
    serializer_class = SignUpSerializer

    @action(detail=False, methods=[variables.POST])
    def sign_up(self, request):

        # Check input data
        required_fields = [variables.PHONE_NUMBER, variables.COUNTRY_CODE]
        if not check_api_input_data(request, required_fields):
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=True, data={variables.DATA: None, variables.MESSAGE: INVALID_INPUT_DATA},)

        # Validate Input data
        phone_number = request.data.get(variables.PHONE_NUMBER)
        country_code = request.data.get(variables.COUNTRY_CODE)
        if not country_code_validator(country_code):
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=True, data=INVALID_INPUT_DATA)
        if not PhoneNumberValidatorAdapter(phone_number, country_code).validate():
            return BaseResponse(
                data={variables.Data: serializer.errors, variables.MESSAGE: f"{INVALID_PHONE_NUMBER}. The supported formet for selected country is: {countries_hints_dict[country_code]}"},
                is_exception=True,
                status=status.HTTP_400_BAD_REQUEST,
            )
        normalized_phone_number = normilize_phone_number(
            phone_number, country_code=country_code)
        validated_data = {
            variables.PHONE_NUMBER: normalized_phone_number,
            variables.COUNTRY_CODE: country_code
        }

        # Send data to serializer
        serializer = self.get_serializer_class()(data=validated_data)
        if not serializer.is_valid():
            return Response(
                data={variables.Data: serializer.errors, variables.MESSAGE: INVALID_INPUT_DATA},
                is_exception=True,
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        # Sign up user
        user = serializer.user_exists(
            phone_number=normalized_phone_number)  # returns user or none
        if user:
            return BaseResponse(
                data={variables.DATA: None, variables.MESSAGE: USER_ALREADY_EXISTS},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            user = serializer.create_user(phone_number=normalized_phone_number)
            return BaseResponse(
                data={variables.DATA: None, variables.MESSAGE: USER_REGISTERD},
                status=status.HTTP_201_CREATED,
            )


class AnonymousUserViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def generate_token(self, request):
        """
        Generate and return an anonymous access token.

        Parameters:
        ----------
        request: HttpRequest
            The Django HttpRequest object.

        Returns:
        ----------
        Response
            The response containing the generated anonymous access token.
        """
        if not isinstance(request.user, AnonymousUser):
            return BaseResponse(
                message=MUST_BE_ANON,
                data=None,
                is_exception=True,
                http_status_code=status.HTTP_400_BAD_REQUEST,
                business_status_code=BUSINESS_STATUS.USER_DONT_HAVE_ACCESS,
            )
        try:
            access = generate_token(request)[variables.ANON_TOKEN]
            return BaseResponse(
                message=ANON_TOKEN_CREATED,
                data=access,
                is_exception=False,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.SUCCESS,
            )
        except Exception as e:
            return Response(
                data=str(e),
                is_exception=True,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginViewSet(
    viewsets.GenericViewSet,
):
    """
    API endpoint that provides various actions related to Login.

    Attributes
    ----------
    * `queryset`: ``QuerySet``
        The set of all User objects.
    """
    queryset = User.objects.all()
    permission_classes = [AnonymousTokenPermission]
    serializer_class = LoginSerializer

    @action(detail=False, methods=[variables.POST])
    def login(self, request):
        """
        Logs in a user by verifying the provided phone number and verification code.

        This endpoint is used to log in a user by verifying the provided phone number and verification code against stored data.
        If the verification is successful, authentication tokens are generated and returned.

        Parameters
        ----------
        request : Request
            The HTTP request object containing the phone_number and verification_code in the data field.

        Returns
        -------
        Response
            A response indicating the success or failure of the login operation, along with authentication tokens if successful.
        """

        # Check input data
        required_fields = [variables.PHONE_NUMBER,
                           variables.VERIFICATION_CODE, variables.COUNTRY_CODE]
        if not check_api_input_data(request, required_fields):
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=True, data=INVALID_INPUT_DATA)

        # Validate Input data
        phone_number = request.data.get(variables.PHONE_NUMBER)
        country_code = request.data.get(variables.COUNTRY_CODE)
        if not country_code_validator(country_code):
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=True, data=INVALID_INPUT_DATA)
        if not PhoneNumberValidatorAdapter(phone_number, country_code).validate():
            return BaseResponse(
                http_status_code=status.HTTP_400_BAD_REQUEST,
                is_exception=True,
                message=f"{INVALID_PHONE_NUMBER}. The supported formet for selected country is: {countries_hints_dict[country_code]}",
                data=None,
                business_status_code=BUSINESS_STATUS.INVALID_INPUT_DATA,
            )
        normalized_phone_number = normilize_phone_number(
            phone_number, country_code)
        verification_code = request.data.get(variables.VERIFICATION_CODE)
        validated_data = {
            variables.PHONE_NUMBER: normalized_phone_number,
            variables.COUNTRY_CODE: country_code,
            variables.VERIFICATION_CODE: verification_code}

        # Send data to serializer
        serializer = self.get_serializer_class()(data=validated_data)
        if not serializer.is_valid():
            return BaseResponse(
                message=INVALID_INPUT_DATA,
                data={variables.DETAILS: serializer.errors},
                is_exception=True,
                http_status_code=status.HTTP_400_BAD_REQUEST,
                business_status_code=BUSINESS_STATUS.INVALID_INPUT_DATA,
            )

        # Send access token
        user = serializer.user_exists(phone_number=normalized_phone_number)
        if not user:
            return BaseResponse(
                message=USER_DOSE_NOT_EXISTS,
                data=None,
                is_exception=True,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.USER_NOT_FOUND,)

        if user.is_bocked:
            return BaseResponse(
                message=BLOCKED_USER,
                data=None,
                is_exception=True,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.USER_IS_BLOCKED,
            )
        try:
            original_otp_data = serializer.get_original_otp(user)
        except redis.ConnectionError:
            # TODO add this to a log server
            return BaseResponse(
                data=None,
                message=variables.TRY_AGAIN_LATER,
                is_exception=True,
                business_status_code=BUSINESS_STATUS.REDIS_IS_DOWN,
                http_status_code=status.HTTP_200_OK
            )
        if not login_otp_validator(user, validated_data[variables.VERIFICATION_CODE], original_otp_data, serializer):
            return BaseResponse(
                message=INVALID_OTP,
                is_exception=True,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.INVALID_LOGIN_CREDENTIONAL,)

        tokens = get_token_for_user(user, serializer, request)
        try:
            serializer.remove_otp_from_redis(user)
        except redis.ConnectionError:
            return BaseResponse(
                data=None,
                message=variables.TRY_AGAIN_LATER,
                is_exception=True,
                business_status_code=BUSINESS_STATUS.REDIS_IS_DOWN,
                http_status_code=status.HTTP_200_OK
            )
        return BaseResponse(
            message=USER_LOGGED_IN,
            data={
                variables.REFRESH_TOKEN: str(tokens[variables.REFRESH]),
                variables.ACCESS_TOKEN: str(tokens[variables.ACCESS]),
            },
            is_exception=False,
            http_status_code=status.HTTP_200_OK,
            business_status_code=BUSINESS_STATUS.SUCCESS,)

    @action(detail=False, methods=[variables.POST], serializer_class=None)
    def logout(self, request):
        """
        Log out the current user.

        Parameters:
        ----------
        * `request`: ``HttpRequest``
            The Django HttpRequest object.

        Returns:
        ----------
        ``Response``
            The response indicating the success or failure of the logout process.
        """
        if isinstance(request.user, AnonymousUser):
            return Response(status=status.HTTP_400_BAD_REQUEST, data=None)

        return BaseResponse(
            message=USER_LOGGED_OUT,
            data=None,
            is_exception=False,
            http_status_code=status.HTTP_200_OK,
            business_status_code=BUSINESS_STATUS.SUCCESS,
        )


class TokenRefreshWithPermission(TokenRefreshView):
    """
    Token refresh view with anonymous token permission.

    Attributes:
    ----------
    * `permission_classes`: ``list``
        List of permissions required for token refresh.
    """
    permission_classes = [AnonymousTokenPermission]




            # if user.is_bocked:
            #     return BaseResponse(
            #         message=BLOCKED_USER,
            #         data=None,
            #         is_exception=True,
            #         http_status_code=status.HTTP_200_OK,
            #         business_status_code=BUSINESS_STATUS.USER_IS_BLOCKED,
            #     )
