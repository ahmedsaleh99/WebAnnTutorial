import uuid

from annotations.models import (
    AnnotationDimension,
    AnnotationLabel,
    Project,
    ProjectTemplate,
    Subject,
)


def create_template(**overrides) -> ProjectTemplate:
    values = {
        "name": "Conversation",
        "key": f"template-{uuid.uuid4().hex[:8]}",
        "version": 1,
    }
    values.update(overrides)
    return ProjectTemplate.objects.create(**values)


def create_project(**overrides) -> Project:
    values = {
        "name": "Example project",
        "key": f"project-{uuid.uuid4().hex[:8]}",
    }
    values.update(overrides)
    if "template" not in values:
        values["template"] = create_template()
    return Project.objects.create(**values)


def create_dimension(**overrides) -> AnnotationDimension:
    values = {"name": "Activity", "key": "activity"}
    values.update(overrides)
    if "project" not in values:
        values["project"] = create_project()
    return AnnotationDimension.objects.create(**values)


def create_label(**overrides) -> AnnotationLabel:
    values = {"name": "Speaking"}
    values.update(overrides)
    if "dimension" not in values:
        values["dimension"] = create_dimension()
    return AnnotationLabel.objects.create(**values)


def create_subject(**overrides) -> Subject:
    values = {"subject_id": "subject-001"}
    values.update(overrides)
    if "project" not in values:
        values["project"] = create_project()
    return Subject.objects.create(**values)
