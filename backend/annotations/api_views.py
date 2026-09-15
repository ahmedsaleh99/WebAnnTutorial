from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import (
    AnnotationDimension,
    AnnotationJob,
    AnnotationLabel,
    AnnotationResult,
    AnnotationWorkItem,
    Project,
    ProjectTemplate,
    Subject,
    Task,
    VideoAsset,
    VideoView,
)
from .permissions import (
    IsAdminOrReadOnly,
    IsManagerOrAssignedAnnotator,
    IsManagerOrReadOnlyWorkflow,
)
from .serializers import (
    AnnotationDimensionSerializer,
    AnnotationJobSerializer,
    AnnotationLabelSerializer,
    AnnotationResultSerializer,
    AnnotationWorkItemSerializer,
    ProjectSerializer,
    ProjectTemplateSerializer,
    SubjectSerializer,
    TaskSerializer,
    VideoAssetSerializer,
    VideoViewSerializer,
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


class AssignedWorkflowQuerysetMixin:
    """Scope workflow reads in SQL before DRF retrieves or serializes objects."""

    def scope_to_user(self, queryset, assignment_path):
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(**{assignment_path: user}).distinct()


class TaskViewSet(AssignedWorkflowQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsManagerOrReadOnlyWorkflow]

    def get_queryset(self):
        queryset = Task.objects.select_related(
            "project", "created_by"
        ).prefetch_related("subjects")
        queryset = self.scope_to_user(queryset, "jobs__assigned_to")
        if project_id := self.request.query_params.get("project"):
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class VideoAssetViewSet(AssignedWorkflowQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = VideoAssetSerializer
    permission_classes = [IsManagerOrReadOnlyWorkflow]

    def get_queryset(self):
        queryset = VideoAsset.objects.select_related("project")
        return self.scope_to_user(queryset, "video_views__task__jobs__assigned_to")


class VideoViewViewSet(AssignedWorkflowQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = VideoViewSerializer
    permission_classes = [IsManagerOrReadOnlyWorkflow]

    def get_queryset(self):
        queryset = VideoView.objects.select_related("task", "asset", "subject")
        return self.scope_to_user(queryset, "task__jobs__assigned_to")


class AnnotationJobViewSet(AssignedWorkflowQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = AnnotationJobSerializer
    permission_classes = [IsManagerOrAssignedAnnotator]

    def get_queryset(self):
        queryset = AnnotationJob.objects.select_related(
            "task", "assigned_to", "created_by"
        ).prefetch_related("work_items__task_subject__subject")
        return self.scope_to_user(queryset, "assigned_to")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AnnotationWorkItemViewSet(AssignedWorkflowQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = AnnotationWorkItemSerializer
    permission_classes = [IsManagerOrAssignedAnnotator]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        queryset = AnnotationWorkItem.objects.select_related(
            "job__assigned_to", "task_subject__subject", "task_subject__task"
        )
        return self.scope_to_user(queryset, "job__assigned_to")


class AnnotationResultViewSet(AssignedWorkflowQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = AnnotationResultSerializer
    permission_classes = [IsManagerOrAssignedAnnotator]

    def get_queryset(self):
        queryset = AnnotationResult.objects.select_related(
            "work_item__job__assigned_to"
        )
        return self.scope_to_user(queryset, "work_item__job__assigned_to")

    def perform_create(self, serializer):
        work_item = serializer.validated_data["work_item"]
        if (
            not self.request.user.is_staff
            and work_item.job.assigned_to_id != self.request.user.id
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("This work item is not assigned to you.")
        serializer.save()
