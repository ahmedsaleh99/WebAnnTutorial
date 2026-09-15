from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import UserSecurity


def user_data(user):
    try:
        must_change_password = user.security_settings.must_change_password
    except ObjectDoesNotExist:
        must_change_password = False

    if user.is_superuser:
        role = "admin"
    elif user.is_staff:
        role = "manager"
    else:
        role = "annotator"

    return {
        "id": user.pk,
        "username": user.get_username(),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": role,
        "must_change_password": must_change_password,
    }


def set_media_cookie(response, token_key):
    response.set_cookie(
        "webann_media_token",
        token_key,
        httponly=True,
        secure=settings.WEBANN_SECURE_COOKIES,
        samesite="Strict",
        max_age=60 * 60 * 8,
    )
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = str(request.data.get("username", ""))
    password = str(request.data.get("password", ""))
    user = authenticate(request, username=username, password=password)

    if user is None or not user.is_active:
        return Response(
            {"detail": "Invalid username or password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token, _ = Token.objects.get_or_create(user=user)
    response = Response({"token": token.key, "user": user_data(user)})
    return set_media_cookie(response, token.key)


@api_view(["GET"])
def current_user(request):
    return Response(user_data(request.user))


@api_view(["POST"])
def change_password(request):
    current_password = str(request.data.get("current_password", ""))
    new_password = str(request.data.get("new_password", ""))
    confirmation = str(request.data.get("new_password_confirmation", ""))

    if not request.user.check_password(current_password):
        return Response(
            {"detail": "The current password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if new_password != confirmation:
        return Response(
            {"detail": "The new passwords do not match."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(new_password, user=request.user)
    except ValidationError as error:
        return Response(
            {"detail": " ".join(error.messages)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])
    security, _ = UserSecurity.objects.get_or_create(user=request.user)
    security.must_change_password = False
    security.save(update_fields=["must_change_password", "updated_at"])

    if request.auth:
        request.auth.delete()
    token = Token.objects.create(user=request.user)
    response = Response({"token": token.key, "user": user_data(request.user)})
    return set_media_cookie(response, token.key)


@api_view(["POST"])
def logout(request):
    if request.auth:
        request.auth.delete()
    response = Response(status=status.HTTP_204_NO_CONTENT)
    response.delete_cookie("webann_media_token", samesite="Strict")
    return response


@api_view(["GET"])
@permission_classes([AllowAny])
def authorize_media(request):
    token_key = request.COOKIES.get("webann_media_token", "")
    try:
        user = Token.objects.select_related("user").get(key=token_key).user
    except (Token.DoesNotExist, ValueError):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    return Response(status=status.HTTP_204_NO_CONTENT)
