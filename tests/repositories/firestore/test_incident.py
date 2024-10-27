import contextlib
import os
from dataclasses import asdict
from datetime import UTC
from typing import cast
from unittest import skipUnless

import requests
from faker import Faker
from google.api_core.exceptions import AlreadyExists
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import CollectionReference
from unittest_parametrize import ParametrizedTestCase, parametrize

from models import HistoryEntry, Incident
from repositories.firestore import FirestoreIncidentRepository
from tests.util import create_random_history_entry, create_random_incident

FIRESTORE_DATABASE = '(default)'


@skipUnless('FIRESTORE_EMULATOR_HOST' in os.environ, 'Firestore emulator not available')
class TestClient(ParametrizedTestCase):
    def setUp(self) -> None:
        self.faker = Faker()

        # Reset Firestore emulator before each test
        requests.delete(
            f'http://{os.environ["FIRESTORE_EMULATOR_HOST"]}/emulator/v1/projects/google-cloud-firestore-emulator/databases/{FIRESTORE_DATABASE}/documents',
            timeout=5,
        )

        self.repo = FirestoreIncidentRepository(FIRESTORE_DATABASE)
        self.client = FirestoreClient(database=FIRESTORE_DATABASE)

    def add_random_incidents(
        self, n: int, client_id: str | None = None, reported_by: str | None = None, assigned_to: str | None = None
    ) -> list[Incident]:
        incidents: list[Incident] = []

        # Add n incidents to Firestore
        for _ in range(n):
            incident = create_random_incident(
                self.faker, client_id=client_id, reported_by=reported_by, assigned_to=assigned_to
            )

            incidents.append(incident)
            incident_dict = asdict(incident)
            del incident_dict['id']
            del incident_dict['client_id']

            client_ref = self.client.collection('clients').document(incident.client_id)
            with contextlib.suppress(AlreadyExists):
                client_ref.create({})

            incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident.id)
            incident.last_modified = self.faker.past_datetime(tzinfo=UTC)  # type: ignore[attr-defined]
            incident_dict['last_modified'] = incident.last_modified  # type: ignore[attr-defined]
            incident_ref.create(incident_dict)

        return incidents

    def add_random_history_entries(
        self, n: int, client_id: str | None = None, incident_id: str | None = None
    ) -> list[HistoryEntry]:
        entries: list[HistoryEntry] = []

        # Add n history entries to Firestore
        for i in range(n):
            history_entry = create_random_history_entry(self.faker, seq=i, client_id=client_id, incident_id=incident_id)
            entries.append(history_entry)
            history_entry_dict = asdict(history_entry)
            del history_entry_dict['incident_id']
            del history_entry_dict['client_id']

            client_ref = self.client.collection('clients').document(history_entry.client_id)
            incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(history_entry.incident_id)
            history_ref = cast(CollectionReference, incident_ref.collection('history')).document(str(i))
            history_ref.create(history_entry_dict)
            incident_ref.update({'last_modified': history_entry.date})

        return entries

    @parametrize(
        ['field', 'offset', 'limit'],
        [
            ('reported_by', None, None),
            ('reported_by', None, 3),
            ('reported_by', 2, None),
            ('reported_by', 2, 2),
            ('assigned_to', None, None),
            ('assigned_to', None, 3),
            ('assigned_to', 2, None),
            ('assigned_to', 2, 2),
        ],
    )
    def test_get_all_by_field(self, field: str, offset: int | None, limit: int | None) -> None:
        client_id = cast(str, self.faker.uuid4())
        reporter_id = cast(str, self.faker.uuid4())
        assignee_id = cast(str, self.faker.uuid4())

        self.add_random_incidents(3, client_id=client_id)
        incidents = self.add_random_incidents(5, client_id=client_id, reported_by=reporter_id, assigned_to=assignee_id)

        if field == 'reported_by':
            result = list(
                self.repo.get_all_by_reporter(client_id=client_id, reporter_id=reporter_id, offset=offset, limit=limit)
            )
        else:
            result = list(
                self.repo.get_all_by_assignee(client_id=client_id, assignee_id=assignee_id, offset=offset, limit=limit)
            )

        incidents.sort(key=lambda i: i.last_modified, reverse=True)  # type: ignore[attr-defined]

        if offset is not None:
            incidents = incidents[offset:]

        if limit is not None:
            incidents = incidents[:limit]

        self.assertEqual(result, incidents)

    @parametrize(
        'field',
        [
            ('assigned_to',),
        ],
    )
    def test_count_by_field(self, field: str) -> None:
        client_id = cast(str, self.faker.uuid4())
        reporter_id = cast(str, self.faker.uuid4())
        assignee_id = cast(str, self.faker.uuid4())

        self.add_random_incidents(3, client_id=client_id)
        incidents = self.add_random_incidents(3, client_id=client_id, reported_by=reporter_id, assigned_to=assignee_id)

        if field == 'assigned_to':
            result = self.repo.count_by_assignee(client_id=client_id, assignee_id=assignee_id)

        self.assertEqual(result, len(incidents))

    def test_get_history(self) -> None:
        client_id = cast(str, self.faker.uuid4())
        reporter_id = cast(str, self.faker.uuid4())

        incident = self.add_random_incidents(1, client_id=client_id, reported_by=reporter_id)[0]
        entries = self.add_random_history_entries(3, client_id=client_id, incident_id=incident.id)

        result = list(self.repo.get_history(client_id=client_id, incident_id=incident.id))

        self.assertEqual(result, entries)
