from unittest import TestCase

from app import create_app


class TestInciden(TestCase):
    def setUp(self) -> None:
        app = create_app()
        self.client = app.test_client()

    def test_user_incidents(self) -> None:
        resp = self.client.get('/api/v1/users/me/incidents')

        self.assertEqual(resp.status_code, 200)

    def test_employee_incidents(self) -> None:
        resp = self.client.get('/api/v1/employees/me/incidents')

        self.assertEqual(resp.status_code, 200)
