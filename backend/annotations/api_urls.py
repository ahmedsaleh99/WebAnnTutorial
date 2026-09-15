from django.urls import path
from rest_framework.routers import DefaultRouter

from .api_views import (
    AnnotationDimensionViewSet,
    AnnotationJobViewSet,
    AnnotationLabelViewSet,
    AnnotationResultViewSet,
    AnnotationWorkItemViewSet,
    ProjectTemplateViewSet,
    ProjectViewSet,
    SubjectViewSet,
    TaskViewSet,
    VideoAssetViewSet,
    VideoViewViewSet,
)
from .auth_views import authorize_media, change_password, current_user, login, logout

router = DefaultRouter()
router.register("templates", ProjectTemplateViewSet, basename="template")
router.register("projects", ProjectViewSet, basename="project")
router.register("dimensions", AnnotationDimensionViewSet, basename="dimension")
router.register("labels", AnnotationLabelViewSet, basename="label")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("tasks", TaskViewSet, basename="task")
router.register("video-assets", VideoAssetViewSet, basename="video-asset")
router.register("video-views", VideoViewViewSet, basename="video-view")
router.register("jobs", AnnotationJobViewSet, basename="job")
router.register("work-items", AnnotationWorkItemViewSet, basename="work-item")
router.register("results", AnnotationResultViewSet, basename="result")

urlpatterns = [
    path("auth/login/", login, name="login"),
    path("auth/me/", current_user, name="current-user"),
    path("auth/password-change/", change_password, name="password-change"),
    path("auth/logout/", logout, name="logout"),
    path("auth/media/authorize/", authorize_media, name="authorize-media"),
    *router.urls,
]
