from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from annotations.models import (
    AnnotationDimension,
    AnnotationLabel,
    Project,
    ProjectTemplate,
    Subject,
    VideoView,
)

from .builders import (
    create_dimension,
    create_job,
    create_label,
    create_project,
    create_result,
    create_subject,
    create_task,
    create_template,
    create_video_asset,
    create_video_view,
)


class ProjectTemplateTests(TestCase):
    def test_key_and_version_are_unique_together(self):
        create_template(key="conversation", version=1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ProjectTemplate.objects.create(
                name="Duplicate", key="conversation", version=1
            )

    def test_template_in_use_cannot_be_deleted(self):
        project = create_project()

        with self.assertRaises(ProtectedError):
            project.template.delete()


class ProjectTests(TestCase):
    def test_invalid_status_fails_model_validation(self):
        project = Project(
            name="Invalid project",
            key="invalid-project",
            template=create_template(),
            status="unknown",
        )

        with self.assertRaises(ValidationError):
            project.full_clean()


class AnnotationStructureTests(TestCase):
    def test_dimension_keys_are_unique_inside_a_project(self):
        dimension = create_dimension()

        with self.assertRaises(IntegrityError), transaction.atomic():
            AnnotationDimension.objects.create(
                project=dimension.project, name="Duplicate", key=dimension.key
            )

    def test_same_dimension_key_is_allowed_in_another_project(self):
        first = create_dimension()
        second = create_dimension(key=first.key)

        self.assertNotEqual(first.project, second.project)

    def test_label_names_are_unique_inside_a_dimension(self):
        label = create_label()

        with self.assertRaises(IntegrityError), transaction.atomic():
            AnnotationLabel.objects.create(dimension=label.dimension, name=label.name)

    def test_label_color_must_be_six_digit_hex(self):
        label = create_label(color="purple")

        with self.assertRaises(ValidationError):
            label.full_clean()


class SubjectTests(TestCase):
    def test_subject_ids_are_unique_inside_a_project(self):
        subject = create_subject()

        with self.assertRaises(IntegrityError), transaction.atomic():
            Subject.objects.create(
                project=subject.project, subject_id=subject.subject_id
            )

    def test_deleting_project_cascades_to_owned_configuration(self):
        project = create_project()
        create_dimension(project=project)
        create_subject(project=project)

        project.delete()

        self.assertFalse(Project.objects.filter(pk=project.pk).exists())
        self.assertEqual(AnnotationDimension.objects.count(), 0)
        self.assertEqual(Subject.objects.count(), 0)


class WorkflowModelTests(TestCase):
    def test_video_view_rejects_asset_from_another_project(self):
        task = create_task()
        view = VideoView(
            task=task,
            asset=create_video_asset(),
            name="Foreign camera",
            role=VideoView.Role.MAIN,
        )

        with self.assertRaises(ValidationError):
            view.full_clean()

    def test_subject_view_requires_a_subject_included_in_the_task(self):
        task = create_task()
        subject = create_subject(project=task.project)
        view = VideoView(
            task=task,
            asset=create_video_asset(project=task.project),
            subject=subject,
            name="Subject camera",
            role=VideoView.Role.SUBJECT,
        )

        with self.assertRaises(ValidationError):
            view.full_clean()

    def test_task_has_only_one_main_video(self):
        first_view = create_video_view()

        with self.assertRaises(IntegrityError), transaction.atomic():
            create_video_view(task=first_view.task, role=VideoView.Role.MAIN)

    def test_duplicate_task_assignment_for_annotator_is_rejected(self):
        job = create_job()

        with self.assertRaises(IntegrityError), transaction.atomic():
            create_job(task=job.task, assigned_to=job.assigned_to)

    def test_work_item_has_at_most_one_result(self):
        result = create_result()

        with self.assertRaises(IntegrityError), transaction.atomic():
            create_result(work_item=result.work_item)
