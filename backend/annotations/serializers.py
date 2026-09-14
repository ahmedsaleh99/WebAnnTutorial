from rest_framework import serializers

from .models import (
    AnnotationDimension,
    AnnotationLabel,
    Project,
    ProjectTemplate,
    Subject,
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
