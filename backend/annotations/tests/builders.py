import uuid

from django.contrib.auth import get_user_model

from annotations.models import (
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


def create_task(**overrides) -> Task:
    subjects = overrides.pop("subjects", [])
    values = {"name": "Example task", "key": f"task-{uuid.uuid4().hex[:8]}"}
    values.update(overrides)
    if "project" not in values:
        values["project"] = create_project()
    if "created_by" not in values:
        values["created_by"] = get_user_model().objects.create_user(
            username=f"creator-{uuid.uuid4().hex[:8]}"
        )
    task = Task.objects.create(**values)
    task.subjects.set(subjects)
    return task


def create_video_asset(**overrides) -> VideoAsset:
    values = {"name": "Main camera", "source_type": VideoAsset.SourceType.UPLOAD}
    values.update(overrides)
    if "project" not in values:
        values["project"] = create_project()
    return VideoAsset.objects.create(**values)


def create_video_view(**overrides) -> VideoView:
    values = {"name": "Main view", "role": VideoView.Role.MAIN}
    values.update(overrides)
    if "task" not in values:
        values["task"] = create_task()
    if "asset" not in values:
        values["asset"] = create_video_asset(project=values["task"].project)
    return VideoView.objects.create(**values)


def create_job(**overrides) -> AnnotationJob:
    work_item_status = overrides.pop("work_item_status", None)
    values = {}
    values.update(overrides)
    if "task" not in values:
        values["task"] = create_task()
    if "assigned_to" not in values:
        values["assigned_to"] = get_user_model().objects.create_user(
            username=f"annotator-{uuid.uuid4().hex[:8]}"
        )
    if "created_by" not in values:
        values["created_by"] = values["task"].created_by
    task = values["task"]
    if not task.task_subjects.exists():
        task.subjects.add(create_subject(project=task.project))
    job = AnnotationJob.objects.create(**values)
    for task_subject in task.task_subjects.all():
        AnnotationWorkItem.objects.create(
            job=job,
            task_subject=task_subject,
            **({"status": work_item_status} if work_item_status else {}),
        )
    return job


def create_work_item(**overrides) -> AnnotationWorkItem:
    values = {}
    values.update(overrides)
    if "job" not in values:
        values["job"] = create_job()
    if "task_subject" not in values:
        values["task_subject"] = values["job"].task.task_subjects.first()
    return AnnotationWorkItem.objects.create(**values)


def create_result(**overrides) -> AnnotationResult:
    values = {}
    values.update(overrides)
    if "work_item" not in values:
        job = create_job()
        values["work_item"] = job.work_items.first()
    return AnnotationResult.objects.create(**values)
