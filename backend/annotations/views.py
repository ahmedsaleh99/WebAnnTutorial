from django.http import HttpRequest, JsonResponse


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"service": "api", "status": "ok"})
