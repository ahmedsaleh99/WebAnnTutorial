from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from annotations.models import AnnotationWorkItem

from .builders import (
    create_dimension,
    create_job,
    create_project,
    create_subject,
    create_task,
    create_template,
)


class AuthenticatedAdminApiTestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="api-admin",
            email="admin@example.com",
            password="AdminPassword9!",
        )
        self.client.force_authenticate(self.user)


class TemplateApiTests(AuthenticatedAdminApiTestCase):
    def test_create_and_list_templates_with_stable_response_shapes(self):
        create_response = self.client.post(
            "/api/templates/",
            {"name": "Conversation", "key": "conversation", "version": 1},
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(create_response.data),
            {
                "id",
                "name",
                "key",
                "description",
                "configuration",
                "version",
                "is_active",
                "created_at",
                "updated_at",
            },
        )

        list_response = self.client.get("/api/templates/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(list_response.data), {"count", "next", "previous", "results"}
        )
        self.assertEqual(list_response.data["count"], 1)

    def test_duplicate_key_and_version_returns_validation_error(self):
        create_template(key="conversation", version=1)

        response = self.client.post(
            "/api/templates/",
            {"name": "Duplicate", "key": "conversation", "version": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_template_in_use_returns_conflict_on_delete(self):
        project = create_project()

        response = self.client.delete(f"/api/templates/{project.template_id}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data,
            {"detail": "Templates used by projects cannot be deleted."},
        )


class ProjectApiTests(AuthenticatedAdminApiTestCase):
    def test_create_retrieve_update_and_delete_project(self):
        template = create_template()
        create_response = self.client.post(
            "/api/projects/",
            {
                "name": "Study",
                "key": "study",
                "status": "draft",
                "template": str(template.pk),
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        project_id = create_response.data["id"]
        project_url = f"/api/projects/{project_id}/"
        retrieve_response = self.client.get(project_url)

        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data["id"], project_id)
        self.assertEqual(retrieve_response.data["name"], "Study")

        update_response = self.client.patch(
            project_url,
            {"status": "active"},
            format="json",
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["status"], "active")

        delete_response = self.client.delete(project_url)

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_invalid_status_and_unknown_template_return_bad_request(self):
        template = create_template()
        invalid_status_response = self.client.post(
            "/api/projects/",
            {
                "name": "Study",
                "key": "study",
                "status": "unknown",
                "template": str(template.pk),
            },
            format="json",
        )
        unknown_template_response = self.client.post(
            "/api/projects/",
            {
                "name": "Other",
                "key": "other",
                "template": "00000000-0000-0000-0000-000000000000",
            },
            format="json",
        )

        self.assertEqual(
            invalid_status_response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertIn("status", invalid_status_response.data)
        self.assertEqual(
            unknown_template_response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertIn("template", unknown_template_response.data)

    def test_unknown_project_returns_not_found(self):
        response = self.client.get(
            "/api/projects/00000000-0000-0000-0000-000000000000/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_status_filter_returns_only_matching_projects(self):
        create_project(status="draft")
        active_project = create_project(status="active")

        filtered_response = self.client.get("/api/projects/?status=active")

        self.assertEqual(filtered_response.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered_response.data["count"], 1)
        self.assertEqual(
            filtered_response.data["results"][0]["id"], str(active_project.pk)
        )


class ProjectConfigurationApiTests(AuthenticatedAdminApiTestCase):
    def test_create_and_filter_dimensions(self):
        included_project = create_project()
        excluded_project = create_project()
        create_dimension(project=excluded_project)

        create_response = self.client.post(
            "/api/dimensions/",
            {
                "project": str(included_project.pk),
                "name": "Activity",
                "key": "activity",
            },
            format="json",
        )
        filtered_response = self.client.get(
            f"/api/dimensions/?project={included_project.pk}"
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(filtered_response.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered_response.data["count"], 1)
        self.assertEqual(
            filtered_response.data["results"][0]["project"], included_project.pk
        )

    def test_create_label_and_reject_invalid_color(self):
        dimension = create_dimension()
        valid_response = self.client.post(
            "/api/labels/",
            {
                "dimension": str(dimension.pk),
                "name": "Speaking",
                "color": "#112233",
            },
            format="json",
        )
        invalid_response = self.client.post(
            "/api/labels/",
            {"dimension": str(dimension.pk), "name": "Invalid", "color": "blue"},
            format="json",
        )

        self.assertEqual(valid_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("color", invalid_response.data)

    def test_create_and_filter_subjects(self):
        project = create_project()

        create_response = self.client.post(
            "/api/subjects/",
            {
                "project": str(project.pk),
                "subject_id": "student-001",
                "attributes": {"cohort": "A"},
            },
            format="json",
        )
        filtered_response = self.client.get(f"/api/subjects/?project={project.pk}")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(filtered_response.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered_response.data["count"], 1)
        self.assertEqual(
            filtered_response.data["results"][0]["attributes"], {"cohort": "A"}
        )


class WorkflowApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.manager = user_model.objects.create_user(
            username="workflow-manager", password="ManagerPassword9!", is_staff=True
        )
        self.annotator = user_model.objects.create_user(
            username="assigned-annotator", password="AnnotatorPassword9!"
        )
        self.other_annotator = user_model.objects.create_user(
            username="other-annotator", password="AnnotatorPassword9!"
        )

    def test_manager_creates_task_and_server_sets_creator(self):
        project = create_project()
        subject = create_subject(project=project)
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            "/api/tasks/",
            {
                "project": str(project.pk),
                "subjects": [str(subject.pk)],
                "name": "Conversation one",
                "key": "conversation-one",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["created_by"], self.manager.pk)

    def test_job_creates_one_work_item_for_each_task_subject(self):
        project = create_project()
        first_subject = create_subject(project=project, subject_id="first")
        second_subject = create_subject(project=project, subject_id="second")
        task = create_task(
            project=project,
            subjects=[first_subject, second_subject],
            created_by=self.manager,
        )
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            "/api/jobs/",
            {"task": str(task.pk), "assigned_to": self.annotator.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["work_items"]), 2)

    def test_task_rejects_subject_from_another_project(self):
        project = create_project()
        foreign_subject = create_subject()
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            "/api/tasks/",
            {
                "project": str(project.pk),
                "subjects": [str(foreign_subject.pk)],
                "name": "Invalid task",
                "key": "invalid-task",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("subjects", response.data)

    def test_annotator_sees_only_assigned_jobs_and_tasks(self):
        assigned_job = create_job(assigned_to=self.annotator, created_by=self.manager)
        create_job(assigned_to=self.other_annotator, created_by=self.manager)
        self.client.force_authenticate(self.annotator)

        jobs_response = self.client.get("/api/jobs/")
        tasks_response = self.client.get("/api/tasks/")

        self.assertEqual(jobs_response.status_code, status.HTTP_200_OK)
        self.assertEqual(jobs_response.data["count"], 1)
        self.assertEqual(jobs_response.data["results"][0]["id"], str(assigned_job.pk))
        self.assertEqual(tasks_response.data["count"], 1)
        self.assertEqual(
            tasks_response.data["results"][0]["id"], str(assigned_job.task_id)
        )

    def test_unassigned_job_detail_is_hidden_as_not_found(self):
        job = create_job(assigned_to=self.other_annotator, created_by=self.manager)
        self.client.force_authenticate(self.annotator)

        response = self.client.get(f"/api/jobs/{job.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_work_item_status_follows_the_state_machine(self):
        job = create_job(assigned_to=self.annotator, created_by=self.manager)
        work_item = job.work_items.get()
        self.client.force_authenticate(self.annotator)
        work_item_url = f"/api/work-items/{work_item.pk}/"

        invalid_response = self.client.patch(
            work_item_url,
            {"status": AnnotationWorkItem.Status.COMPLETED},
            format="json",
        )
        started_response = self.client.patch(
            work_item_url,
            {"status": AnnotationWorkItem.Status.IN_PROGRESS},
            format="json",
        )
        completed_response = self.client.patch(
            work_item_url,
            {"status": AnnotationWorkItem.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(started_response.status_code, status.HTTP_200_OK)
        self.assertEqual(completed_response.status_code, status.HTTP_200_OK)

    def test_annotator_cannot_reassign_or_delete_a_job(self):
        job = create_job(assigned_to=self.annotator, created_by=self.manager)
        self.client.force_authenticate(self.annotator)
        job_url = f"/api/jobs/{job.pk}/"

        reassign_response = self.client.patch(
            job_url, {"assigned_to": self.other_annotator.pk}, format="json"
        )
        delete_response = self.client.delete(job_url)

        self.assertEqual(reassign_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_manager_can_review_completed_work_item(self):
        job = create_job(
            assigned_to=self.annotator,
            created_by=self.manager,
            work_item_status=AnnotationWorkItem.Status.COMPLETED,
        )
        work_item = job.work_items.get()
        work_item_url = f"/api/work-items/{work_item.pk}/"
        self.client.force_authenticate(self.annotator)

        annotator_response = self.client.patch(
            work_item_url,
            {"status": AnnotationWorkItem.Status.REVIEWED},
            format="json",
        )
        self.client.force_authenticate(self.manager)
        manager_response = self.client.patch(
            work_item_url,
            {"status": AnnotationWorkItem.Status.REVIEWED},
            format="json",
        )

        self.assertEqual(annotator_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(manager_response.status_code, status.HTTP_200_OK)

    def test_annotator_creates_result_only_for_own_work_item(self):
        own_job = create_job(assigned_to=self.annotator, created_by=self.manager)
        other_job = create_job(
            assigned_to=self.other_annotator, created_by=self.manager
        )
        self.client.force_authenticate(self.annotator)

        own_response = self.client.post(
            "/api/results/",
            {
                "work_item": str(own_job.work_items.get().pk),
                "data": {"notes": "done"},
            },
            format="json",
        )
        other_response = self.client.post(
            "/api/results/",
            {"work_item": str(other_job.work_items.get().pk), "data": {}},
            format="json",
        )

        self.assertEqual(own_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(other_response.status_code, status.HTTP_403_FORBIDDEN)
