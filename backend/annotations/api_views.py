from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import (
    AnnotationDimension,
    AnnotationLabel,
    Project,
    ProjectTemplate,
    Subject,
)
from .permissions import IsAdminOrReadOnly
from .serializers import (
    AnnotationDimensionSerializer,
    AnnotationLabelSerializer,
    ProjectSerializer,
    ProjectTemplateSerializer,
    SubjectSerializer,
)


class ProjectTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProjectTemplate.objects.all()
    serializer_class = ProjectTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Templates used by projects cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Project.objects.select_related("template")
        if project_status := self.request.query_params.get("status"):
            queryset = queryset.filter(status=project_status)
        return queryset


class AnnotationDimensionViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationDimensionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = AnnotationDimension.objects.select_related("project")
        if project_id := self.request.query_params.get("project"):
            queryset = queryset.filter(project_id=project_id)
        return queryset


class AnnotationLabelViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationLabelSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = AnnotationLabel.objects.select_related("dimension")
        if dimension_id := self.request.query_params.get("dimension"):
            queryset = queryset.filter(dimension_id=dimension_id)
        return queryset


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Subject.objects.select_related("project")
        if project_id := self.request.query_params.get("project"):
            queryset = queryset.filter(project_id=project_id)
        return queryset
