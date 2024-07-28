from django.utils.translation import gettext_lazy as _

PHONE_NUMBER_VERBOSE_NAME = 'Phone number'
STATE_VERBOSE_NAME = "State"
CREATED_AT_VERBOSE_NAME = "Created at"
USER_PERMISSIONS_VERBOSE_NAME = "Us
er Permissions"
PENDING = "pending"
PHONE_VERIFIED = "phone_verified"
DELETED = "deleted"

USER_STATE = (
    (variables.PENDING, _("Pending")),
    (variables.PHONE_VERIFIED, _("Phone number Verified")),
    (variables.DELETED, _("Deleted")),
)