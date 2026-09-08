import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler to standardize API error responses
    and protect against leaking unhandled internal tracebacks in production.
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response

    logger.error(f"Unhandled server exception in API: {exc}", exc_info=True)

    if settings.DEBUG:
        return None

    return Response(
        {
            "error": "InternalServerError",
            "detail": "An internal server error occurred. Please try again later."
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
