from django.urls import include, path

urlpatterns = [
    path("", include("annotations.urls")),
    path("api/", include("annotations.api_urls")),
]
