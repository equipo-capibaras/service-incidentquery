import logging
from collections.abc import Generator
from enum import Enum
from typing import Any, cast

import dacite
from google.cloud.firestore import Client as FirestoreClient  # type: ignore[import-untyped]
from google.cloud.firestore_v1 import CollectionReference, DocumentReference, DocumentSnapshot, Query
from google.cloud.firestore_v1.aggregation import AggregationQuery
from google.cloud.firestore_v1.base_aggregation import AggregationResult
from google.cloud.firestore_v1.base_query import FieldFilter

from models import HistoryEntry, Incident
from repositories import IncidentRepository


class FirestoreIncidentRepository(IncidentRepository):
    def __init__(self, database: str) -> None:
        self.db = FirestoreClient(database=database)
        self.logger = logging.getLogger(self.__class__.__name__)

    def doc_to_incident(self, doc: DocumentSnapshot) -> Incident:
        client_id = cast(DocumentReference, cast(CollectionReference, cast(DocumentReference, doc.reference).parent).parent).id
        return dacite.from_dict(
            data_class=Incident,
            data={
                **cast(dict[str, Any], doc.to_dict()),
                'id': doc.id,
                'client_id': client_id,
            },
            config=dacite.Config(cast=[Enum]),
        )

    def doc_to_history_entry(self, doc: DocumentSnapshot) -> HistoryEntry:
        incident_ref = cast(DocumentReference, cast(CollectionReference, cast(DocumentReference, doc.reference).parent).parent)
        client_ref = cast(DocumentReference, cast(CollectionReference, incident_ref.parent).parent)
        return dacite.from_dict(
            data_class=HistoryEntry,
            data={
                **cast(dict[str, Any], doc.to_dict()),
                'incident_id': incident_ref.id,
                'client_id': client_ref.id,
            },
            config=dacite.Config(cast=[Enum]),
        )

    def _query_by_field(self, client_id: str, field: str, value: str) -> Query:
        client_ref = self.db.collection('clients').document(client_id)
        incidents_ref = cast(CollectionReference, client_ref.collection('incidents'))
        query = incidents_ref.where(filter=FieldFilter(field, '==', value))  # type: ignore[no-untyped-call]
        return query.order_by('last_modified', direction='DESCENDING')

    def _get_all_by_field(
        self, client_id: str, field: str, value: str, offset: int | None, limit: int | None
    ) -> Generator[Incident, None, None]:
        query = self._query_by_field(client_id, field, value)

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        docs = query.stream()

        for doc in docs:
            yield self.doc_to_incident(doc)

    def get_all_by_reporter(
        self, client_id: str, reporter_id: str, offset: int | None = None, limit: int | None = None
    ) -> Generator[Incident, None, None]:
        return self._get_all_by_field(client_id, 'reported_by', reporter_id, offset, limit)

    def get_all_by_assignee(
        self, client_id: str, assignee_id: str, offset: int | None = None, limit: int | None = None
    ) -> Generator[Incident, None, None]:
        return self._get_all_by_field(client_id, 'assigned_to', assignee_id, offset, limit)

    def count_by_assignee(self, client_id: str, assignee_id: str) -> int:
        query = cast(AggregationQuery, self._query_by_field(client_id, 'assigned_to', assignee_id).count())
        result = cast(list[AggregationResult], query.get()[0])[0]
        return int(result.value)

    def get_history(self, client_id: str, incident_id: str) -> Generator[HistoryEntry, None, None]:
        client_ref = self.db.collection('clients').document(client_id)
        incident_ref = cast(CollectionReference, client_ref.collection('incidents')).document(incident_id)
        history_ref = cast(CollectionReference, incident_ref.collection('history'))
        query = history_ref.order_by('seq', direction='ASCENDING')

        docs = query.stream()

        for doc in docs:
            yield self.doc_to_history_entry(doc)
