from typing import cast
from unittest import TestCase
from unittest.mock import Mock

from faker import Faker

from app import create_app
from models import User
from repositories import UserRepository


class TestIncident(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def test_user_incidents(self) -> None:
        resp = self.client.get('/api/v1/users/me/incidents')

        self.assertEqual(resp.status_code, 200)

    def test_employee_incidents(self) -> None:
        user = User(
            id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            name=self.faker.name(),
            email=self.faker.email(),
        )

        user_repo_mock = Mock(UserRepository)
        cast(Mock, user_repo_mock.get).return_value = user

        with self.app.container.user_repo.override(user_repo_mock):
            resp = self.client.get('/api/v1/employees/me/incidents')

        self.assertEqual(resp.status_code, 200)
