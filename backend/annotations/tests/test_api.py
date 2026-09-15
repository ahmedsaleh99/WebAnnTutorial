from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .builders import create_dimension, create_project, create_template


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
