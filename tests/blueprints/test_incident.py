import base64
import json
from typing import cast
from unittest.mock import Mock

from faker import Faker
from unittest_parametrize import ParametrizedTestCase, parametrize
from werkzeug.test import TestResponse

from app import create_app
from models import Employee, HistoryEntry, InvitationStatus, Role, User
from repositories import EmployeeRepository, IncidentRepository, UserRepository
from tests.util import create_random_history_entry, create_random_incident

from .util import gen_token


class TestIncident(ParametrizedTestCase):
    INCIDENT_API_USER_URL = '/api/v1/users/me/incidents'
    INCIDENT_API_EMPLOYEE_URL = '/api/v1/employees/me/incidents'
    INCIDENT_API_DETAIL_URL = '/api/v1/incidents/{incident_id}'

    def setUp(self) -> None:
        self.faker = Faker()
        self.app = create_app()
        self.client = self.app.test_client()

    def call_incident_api_user(self, token: dict[str, str] | None) -> TestResponse:
        if token is None:
            return self.client.get(self.INCIDENT_API_USER_URL)

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.get(self.INCIDENT_API_USER_URL, headers={'X-Apigateway-Api-Userinfo': token_encoded})

    def call_incident_api_employee(
        self, token: dict[str, str] | None, page_size: int | None = None, page_number: int | None = None
    ) -> TestResponse:
        params = {}
        if page_size is not None:
            params['page_size'] = page_size

        if page_number is not None:
            params['page_number'] = page_number

        if token is None:
            return self.client.get(self.INCIDENT_API_EMPLOYEE_URL, query_string=params)

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.get(
            self.INCIDENT_API_EMPLOYEE_URL, headers={'X-Apigateway-Api-Userinfo': token_encoded}, query_string=params
        )

    def call_incident_detail_api(self, token: dict[str, str] | None, incident_id: str) -> TestResponse:
        if token is None:
            return self.client.get(self.INCIDENT_API_DETAIL_URL.format(incident_id=incident_id))

        token_encoded = base64.urlsafe_b64encode(json.dumps(token).encode()).decode()
        return self.client.get(
            self.INCIDENT_API_DETAIL_URL.format(incident_id=incident_id), headers={'X-Apigateway-Api-Userinfo': token_encoded}
        )

    def test_user_incidents_no_token(self) -> None:
        resp = self.call_incident_api_user(None)

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': 'Token is missing'})

    @parametrize(
        'missing_field',
        [
            ('sub',),
            ('cid',),
            ('role',),
            ('aud',),
        ],
    )
    def test_user_incidents_token_missing_fields(self, missing_field: str) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=Role.USER,
            assigned=True,
        )
        del token[missing_field]
        resp = self.call_incident_api_user(token)

        self.assertEqual(resp.status_code, 401)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 401, 'message': f'{missing_field} is missing in token'})

    def test_user_incidents(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        user_id = cast(str, self.faker.uuid4())

        token = gen_token(
            user_id=user_id,
            client_id=client_id,
            role=Role.USER,
            assigned=True,
        )

        incidents = [create_random_incident(self.faker, client_id=client_id, reported_by=user_id) for _ in range(3)]

        incident_history: dict[str, list[HistoryEntry]] = {}

        for incident in incidents:
            incident_history[incident.id] = [
                create_random_history_entry(self.faker, seq=i, client_id=incident.client_id, incident_id=incident.id)
                for i in range(3)
            ]

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get_all_by_reporter).return_value = (x for x in incidents)
        cast(Mock, incident_repo_mock.get_history).side_effect = lambda client_id, incident_id: incident_history[incident_id]  # noqa: ARG005
        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_incident_api_user(token)

        self.assertEqual(resp.status_code, 200)

    def test_employee_incidents(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        employee_id = cast(str, self.faker.uuid4())

        user = User(
            id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            name=self.faker.name(),
            email=self.faker.email(),
        )

        token = gen_token(
            user_id=employee_id,
            client_id=client_id,
            role=Role.AGENT,
            assigned=True,
        )

        incidents = [
            create_random_incident(self.faker, client_id=client_id, assigned_to=employee_id, reported_by=user.id)
            for _ in range(3)
        ]

        incident_history: dict[str, list[HistoryEntry]] = {}

        for incident in incidents:
            incident_history[incident.id] = [
                create_random_history_entry(self.faker, seq=i, client_id=incident.client_id, incident_id=incident.id)
                for i in range(3)
            ]

        user_repo_mock = Mock(UserRepository)
        cast(Mock, user_repo_mock.get).return_value = user

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.count_by_assignee).return_value = len(incidents)
        cast(Mock, incident_repo_mock.get_all_by_assignee).return_value = (x for x in incidents)
        cast(Mock, incident_repo_mock.get_history).side_effect = lambda client_id, incident_id: incident_history[incident_id]  # noqa: ARG005
        with (
            self.app.container.incident_repo.override(incident_repo_mock),
            self.app.container.user_repo.override(user_repo_mock),
        ):
            resp = self.call_incident_api_employee(token, page_size=20, page_number=1)

        self.assertEqual(resp.status_code, 200)

    def test_employee_incidents_invalid_page_size(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        employee_id = cast(str, self.faker.uuid4())

        token = gen_token(
            user_id=employee_id,
            client_id=client_id,
            role=Role.AGENT,
            assigned=True,
        )

        resp = self.call_incident_api_employee(token, page_size=1)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 400, 'message': 'Invalid page_size. Allowed values are [5, 10, 20].'})

    def test_employee_incidents_invalid_page_number(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        employee_id = cast(str, self.faker.uuid4())

        token = gen_token(
            user_id=employee_id,
            client_id=client_id,
            role=Role.AGENT,
            assigned=True,
        )

        resp = self.call_incident_api_employee(token, page_number=0)

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 400, 'message': 'Invalid page_number. Page number must be 1 or greater.'})

    def test_incident_detail_invalid_incident_id(self) -> None:
        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=cast(str, self.faker.uuid4()),
            role=Role.AGENT,
            assigned=True,
        )

        resp = self.call_incident_detail_api(token, 'invalid-incident-id')

        self.assertEqual(resp.status_code, 400)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 400, 'message': 'Invalid incident ID.'})

    def test_incident_detail_not_found(self) -> None:
        incident_id = cast(str, self.faker.uuid4())
        client_id = cast(str, self.faker.uuid4())

        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            role=Role.AGENT,
            assigned=True,
        )

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = None

        with self.app.container.incident_repo.override(incident_repo_mock):
            resp = self.call_incident_detail_api(token, incident_id)

        self.assertEqual(resp.status_code, 404)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data, {'code': 404, 'message': 'Incident not found.'})

    @parametrize(
        ['created_by', 'missing'],
        [
            ('user', None),
            ('agent', None),
            ('user', 'reported_by'),
            ('agent', 'reported_by'),
            ('user', 'created_by'),
            ('agent', 'created_by'),
            ('user', 'assigned_to'),
            ('agent', 'assigned_to'),
        ],
    )
    def test_incident_detail(self, created_by: str, missing: str | None) -> None:
        client_id = cast(str, self.faker.uuid4())

        token = gen_token(
            user_id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            role=Role.AGENT,
            assigned=True,
        )

        user_reported_by = User(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.email(),
        )

        user_created_by = User(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.email(),
        )

        employee_created_by = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.email(),
            role=Role.AGENT,
            invitation_status=InvitationStatus.ACCEPTED,
            invitation_date=self.faker.past_datetime(),
        )

        employee_assigned_to = Employee(
            id=cast(str, self.faker.uuid4()),
            client_id=client_id,
            name=self.faker.name(),
            email=self.faker.email(),
            role=Role.AGENT,
            invitation_status=InvitationStatus.ACCEPTED,
            invitation_date=self.faker.past_datetime(),
        )

        incident = create_random_incident(
            self.faker,
            client_id=client_id,
            reported_by=user_reported_by.id,
            created_by=user_created_by.id if created_by == 'user' else employee_created_by.id,
            assigned_to=employee_assigned_to.id,
        )

        incident_history = [
            create_random_history_entry(self.faker, seq=i, client_id=incident.client_id, incident_id=incident.id)
            for i in range(3)
        ]

        user_repo_mock = Mock(UserRepository)
        cast(Mock, user_repo_mock.get).side_effect = (
            lambda user_id, client_id: user_created_by  # noqa: ARG005
            if user_id == user_created_by.id and created_by == 'user' and missing != 'created_by'
            else user_reported_by
            if user_id == user_reported_by.id and missing != 'reported_by'
            else None
        )
        employee_repo_mock = Mock(EmployeeRepository)
        cast(Mock, employee_repo_mock.get).side_effect = (
            lambda employee_id, client_id: employee_created_by  # noqa: ARG005
            if employee_id == employee_created_by.id and created_by == 'agent' and missing != 'created_by'
            else employee_assigned_to
            if employee_id == employee_assigned_to.id and missing != 'assigned_to'
            else None
        )

        incident_repo_mock = Mock(IncidentRepository)
        cast(Mock, incident_repo_mock.get).return_value = incident
        cast(Mock, incident_repo_mock.get_history).return_value = incident_history

        with (
            self.app.container.incident_repo.override(incident_repo_mock),
            self.app.container.user_repo.override(user_repo_mock),
            self.app.container.employee_repo.override(employee_repo_mock),
        ):
            if missing is not None:
                with self.assertLogs():
                    resp = self.call_incident_detail_api(token, incident.id)
            else:
                resp = self.call_incident_detail_api(token, incident.id)

        cast(Mock, incident_repo_mock.get).assert_called_once_with(client_id=client_id, incident_id=incident.id)

        if missing is not None:
            self.assertEqual(resp.status_code, 500)
            return

        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.get_data())

        self.assertEqual(resp_data['id'], incident.id)
        self.assertEqual(resp_data['name'], incident.name)
        self.assertEqual(resp_data['channel'], incident.channel)

        self.assertEqual(resp_data['reportedBy']['id'], user_reported_by.id)
        self.assertEqual(resp_data['reportedBy']['name'], user_reported_by.name)
        self.assertEqual(resp_data['reportedBy']['email'], user_reported_by.email)
        self.assertEqual(resp_data['reportedBy']['role'], 'user')

        if created_by == 'user':
            self.assertEqual(resp_data['createdBy']['id'], user_created_by.id)
            self.assertEqual(resp_data['createdBy']['name'], user_created_by.name)
            self.assertEqual(resp_data['createdBy']['email'], user_created_by.email)
            self.assertEqual(resp_data['createdBy']['role'], 'user')
        else:
            self.assertEqual(resp_data['createdBy']['id'], employee_created_by.id)
            self.assertEqual(resp_data['createdBy']['name'], employee_created_by.name)
            self.assertEqual(resp_data['createdBy']['email'], employee_created_by.email)
            self.assertEqual(resp_data['createdBy']['role'], 'agent')

        self.assertEqual(resp_data['assignedTo']['id'], employee_assigned_to.id)
        self.assertEqual(resp_data['assignedTo']['name'], employee_assigned_to.name)
        self.assertEqual(resp_data['assignedTo']['email'], employee_assigned_to.email)
        self.assertEqual(resp_data['assignedTo']['role'], 'agent')
