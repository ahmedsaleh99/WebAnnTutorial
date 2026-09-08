from django.test import TestCase
from django.urls import reverse


class HealthEndpointTests(TestCase):
    def test_health_endpoint_reports_that_api_is_ready(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"service": "api", "status": "ok"})
