from rest_framework.routers import DefaultRouter

from .api_views import (
    AnnotationDimensionViewSet,
    AnnotationLabelViewSet,
    ProjectTemplateViewSet,
    ProjectViewSet,
    SubjectViewSet,
)

router = DefaultRouter()
router.register("templates", ProjectTemplateViewSet, basename="template")
router.register("projects", ProjectViewSet, basename="project")
router.register("dimensions", AnnotationDimensionViewSet, basename="dimension")
router.register("labels", AnnotationLabelViewSet, basename="label")
router.register("subjects", SubjectViewSet, basename="subject")

urlpatterns = router.urls
