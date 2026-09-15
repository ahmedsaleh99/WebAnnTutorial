import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class UserSecurity(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="security_settings",
        on_delete=models.CASCADE,
    )
    must_change_password = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Security settings for {self.user.get_username()}"


class ProjectTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    key = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key", "version"]
        constraints = [
            models.UniqueConstraint(
                fields=["key", "version"], name="unique_template_key_version"
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="template_version_at_least_one"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    key = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    template = models.ForeignKey(
        ProjectTemplate, related_name="projects", on_delete=models.PROTECT
    )
    configuration = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "active", "archived"]),
                name="project_status_is_valid",
            )
        ]

    def __str__(self) -> str:
        return self.name


class AnnotationDimension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, related_name="dimensions", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    key = models.SlugField(max_length=100)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "key"], name="unique_dimension_key_per_project"
            )
        ]

    def __str__(self) -> str:
        return f"{self.project}: {self.name}"


class AnnotationLabel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dimension = models.ForeignKey(
        AnnotationDimension, related_name="labels", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    color = models.CharField(
        max_length=7,
        default="#7056d3",
        validators=[RegexValidator(r"^#[0-9a-fA-F]{6}$", "Use a six-digit hex color.")],
    )
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["dimension", "name"],
                name="unique_label_name_per_dimension",
            )
        ]

    def __str__(self) -> str:
        return f"{self.dimension}: {self.name}"


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, related_name="subjects", on_delete=models.CASCADE
    )
    subject_id = models.CharField(max_length=100)
    name = models.CharField(max_length=200, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["subject_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "subject_id"],
                name="unique_subject_id_per_project",
            )
        ]

    def __str__(self) -> str:
        return self.name or self.subject_id


class Task(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        READY = "ready", "Ready"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, related_name="tasks", on_delete=models.CASCADE)
    subjects = models.ManyToManyField(
        Subject, related_name="tasks", through="TaskSubject", blank=True
    )
    name = models.CharField(max_length=200)
    key = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_tasks",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "key"], name="unique_task_key_per_project"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "draft",
                        "ready",
                        "in_progress",
                        "completed",
                        "archived",
                    ]
                ),
                name="task_status_is_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.project}: {self.name}"


class TaskSubject(models.Model):
    """One independently assignable subject within a task."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task, related_name="task_subjects", on_delete=models.CASCADE
    )
    subject = models.ForeignKey(
        Subject, related_name="task_subjects", on_delete=models.PROTECT
    )

    class Meta:
        ordering = ["subject__subject_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["task", "subject"], name="unique_subject_per_task"
            )
        ]

    def clean(self):
        if self.task_id and self.subject_id:
            if self.task.project_id != self.subject.project_id:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    {"subject": "The subject must belong to the task's project."}
                )

    def __str__(self) -> str:
        return f"{self.task}: {self.subject}"


class VideoAsset(models.Model):
    class SourceType(models.TextChoices):
        UPLOAD = "upload", "Local upload"
        REMOTE = "remote", "Remote URL"

    class ProcessingStatus(models.TextChoices):
        UPLOADING = "uploading", "Uploading"
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, related_name="video_assets", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    source_url = models.URLField(max_length=4096, blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.UPLOADING,
    )
    fps = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    frame_count = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.project}: {self.name} ({self.processing_status})"


class VideoView(models.Model):
    class Role(models.TextChoices):
        MAIN = "main", "Main"
        BACK = "back", "Back"
        SUBJECT = "subject", "Subject"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, related_name="video_views", on_delete=models.CASCADE)
    asset = models.ForeignKey(
        VideoAsset, related_name="video_views", on_delete=models.PROTECT
    )
    subject = models.ForeignKey(
        Subject,
        related_name="video_views",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=20, choices=Role.choices)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["task"],
                condition=models.Q(role="main"),
                name="one_main_video_per_task",
            ),
            models.UniqueConstraint(
                fields=["task"],
                condition=models.Q(role="back"),
                name="one_back_video_per_task",
            ),
            models.UniqueConstraint(
                fields=["task", "subject"],
                condition=models.Q(role="subject"),
                name="one_subject_video_per_task_subject",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(role="subject", subject__isnull=False)
                    | (~models.Q(role="subject") & models.Q(subject__isnull=True))
                ),
                name="video_role_matches_subject",
            ),
        ]

    def clean(self):
        errors = {}
        if (
            self.asset_id
            and self.task_id
            and self.asset.project_id != self.task.project_id
        ):
            errors["asset"] = "The asset must belong to the task's project."
        if self.subject_id and self.task_id:
            if self.subject.project_id != self.task.project_id:
                errors["subject"] = "The subject must belong to the task's project."
            elif not self.task.subjects.filter(pk=self.subject_id).exists():
                errors["subject"] = "The subject must be included in the task."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.task}: {self.name}"


class AnnotationJob(models.Model):
    """A parent assignment grouping one work item per task subject."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, related_name="jobs", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="annotation_jobs",
        on_delete=models.PROTECT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_annotation_jobs",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["task", "assigned_to"],
                name="unique_job_per_task_annotator",
            )
        ]

    def __str__(self) -> str:
        return f"{self.task} assigned to {self.assigned_to}"


class AnnotationWorkItem(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        REVIEWED = "reviewed", "Reviewed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        AnnotationJob, related_name="work_items", on_delete=models.CASCADE
    )
    task_subject = models.ForeignKey(
        TaskSubject,
        related_name="work_items",
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ASSIGNED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "task_subject"],
                name="unique_work_item_per_job_subject",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["assigned", "in_progress", "completed", "reviewed"]
                ),
                name="annotation_work_item_status_is_valid",
            ),
        ]

    def clean(self):
        if self.job_id and self.task_subject_id:
            if self.job.task_id != self.task_subject.task_id:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    {"task_subject": "The work item must belong to the job's task."}
                )

    def __str__(self) -> str:
        return f"{self.job}: {self.task_subject.subject}"


class AnnotationResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_item = models.OneToOneField(
        AnnotationWorkItem, related_name="result", on_delete=models.CASCADE
    )
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Result for {self.work_item}"
