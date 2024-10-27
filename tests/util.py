from datetime import UTC
from typing import cast

from faker import Faker

from models import Action, Channel, HistoryEntry, Incident


def create_random_incident(faker: Faker, *, client_id: str | None = None, reported_by: str | None = None) -> Incident:
    return Incident(
        id=cast(str, faker.uuid4()),
        client_id=client_id or cast(str, faker.uuid4()),
        name=faker.sentence(3),
        channel=faker.random_element(list(Channel)),
        reported_by=reported_by or cast(str, faker.uuid4()),
        created_by=cast(str, faker.uuid4()),
        assigned_to=cast(str, faker.uuid4()),
    )


def create_random_history_entry(
    faker: Faker, *, seq: int, client_id: str | None = None, incident_id: str | None = None
) -> HistoryEntry:
    return HistoryEntry(
        incident_id=incident_id or cast(str, faker.uuid4()),
        client_id=client_id or cast(str, faker.uuid4()),
        date=faker.past_datetime(tzinfo=UTC),
        action=faker.random_element(list(Action)),
        description=faker.text(),
        seq=seq,
    )
