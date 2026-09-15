from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

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


class ProjectTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTemplate
        fields = [
            "id",
            "name",
            "key",
            "description",
            "configuration",
            "version",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "key",
            "description",
            "status",
            "template",
            "configuration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AnnotationDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnotationDimension
        fields = ["id", "project", "name", "key", "position"]
        read_only_fields = ["id"]


class AnnotationLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnotationLabel
        fields = ["id", "dimension", "name", "color", "position"]
        read_only_fields = ["id"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id",
            "project",
            "subject_id",
            "name",
            "attributes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    subjects = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Subject.objects.all(), required=False
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "subjects",
            "name",
            "key",
            "description",
            "instructions",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate(self, attributes):
        project = attributes.get("project", getattr(self.instance, "project", None))
        subjects = attributes.get("subjects", [])
        if project and any(subject.project_id != project.id for subject in subjects):
            raise serializers.ValidationError(
                {"subjects": "Every subject must belong to the task's project."}
            )
        return attributes


class VideoAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoAsset
        fields = [
            "id",
            "project",
            "name",
            "source_type",
            "source_url",
            "processing_status",
            "fps",
            "frame_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VideoViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoView
        fields = ["id", "task", "asset", "subject", "name", "role", "position"]
        read_only_fields = ["id"]

    def validate(self, attributes):
        role = attributes.get("role", getattr(self.instance, "role", None))
        subject = attributes.get("subject", getattr(self.instance, "subject", None))
        if role == VideoView.Role.SUBJECT and subject is None:
            raise serializers.ValidationError(
                {"subject": "A subject video must identify its subject."}
            )
        if role != VideoView.Role.SUBJECT and subject is not None:
            raise serializers.ValidationError(
                {"subject": "Only a subject video may identify a subject."}
            )
        instance = VideoView(
            **{
                "task": attributes.get("task", getattr(self.instance, "task", None)),
                "asset": attributes.get("asset", getattr(self.instance, "asset", None)),
                "subject": attributes.get(
                    "subject", getattr(self.instance, "subject", None)
                ),
                "name": attributes.get("name", getattr(self.instance, "name", "")),
                "role": attributes.get("role", getattr(self.instance, "role", "")),
                "position": attributes.get(
                    "position", getattr(self.instance, "position", 0)
                ),
            }
        )
        try:
            instance.full_clean(
                exclude=["id"], validate_unique=False, validate_constraints=False
            )
        except Exception as error:
            if isinstance(error, ValidationError):
                raise serializers.ValidationError(error.message_dict) from error
            raise
        return attributes


class AnnotationWorkItemSerializer(serializers.ModelSerializer):
    TRANSITIONS = {
        AnnotationWorkItem.Status.ASSIGNED: {AnnotationWorkItem.Status.IN_PROGRESS},
        AnnotationWorkItem.Status.IN_PROGRESS: {AnnotationWorkItem.Status.COMPLETED},
        AnnotationWorkItem.Status.COMPLETED: {AnnotationWorkItem.Status.REVIEWED},
        AnnotationWorkItem.Status.REVIEWED: set(),
    }

    class Meta:
        model = AnnotationWorkItem
        fields = [
            "id",
            "job",
            "task_subject",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "job", "task_subject", "created_at", "updated_at"]

    def validate(self, attributes):
        if self.instance and "status" in attributes:
            old_status = self.instance.status
            new_status = attributes["status"]
            if (
                new_status != old_status
                and new_status not in self.TRANSITIONS[old_status]
            ):
                raise serializers.ValidationError(
                    {"status": f"Cannot move from {old_status} to {new_status}."}
                )
            if (
                new_status == AnnotationWorkItem.Status.REVIEWED
                and not self.context["request"].user.is_staff
            ):
                raise serializers.ValidationError(
                    {"status": "Only a manager may mark a job as reviewed."}
                )
        return attributes


class AnnotationJobSerializer(serializers.ModelSerializer):
    work_items = AnnotationWorkItemSerializer(many=True, read_only=True)

    class Meta:
        model = AnnotationJob
        fields = [
            "id",
            "task",
            "assigned_to",
            "created_by",
            "work_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "work_items",
            "created_at",
            "updated_at",
        ]

    def validate_task(self, task):
        if not task.task_subjects.exists():
            raise serializers.ValidationError(
                "Select at least one task subject before creating an assignment."
            )
        return task

    @transaction.atomic
    def create(self, validated_data):
        job = AnnotationJob.objects.create(**validated_data)
        AnnotationWorkItem.objects.bulk_create(
            [
                AnnotationWorkItem(job=job, task_subject=task_subject)
                for task_subject in job.task.task_subjects.all()
            ]
        )
        return job


class AnnotationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnotationResult
        fields = ["id", "work_item", "data", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
