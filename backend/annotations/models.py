import uuid

from django.core.validators import RegexValidator
from django.db import models


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
