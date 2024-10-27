from collections.abc import Generator

from models import HistoryEntry, Incident


class IncidentRepository:
    def get_all_by_reporter(
        self, client_id: str, reporter_id: str, offset: int | None = None, limit: int | None = None
    ) -> Generator[Incident, None, None]:
        raise NotImplementedError  # pragma: no cover

    def get_all_by_assignee(
        self, client_id: str, assignee_id: str, offset: int | None = None, limit: int | None = None
    ) -> Generator[Incident, None, None]:
        raise NotImplementedError  # pragma: no cover

    def count_by_assignee(self, client_id: str, assignee_id: str) -> int:
        raise NotImplementedError  # pragma: no cover

    def get_history(self, client_id: str, incident_id: str) -> Generator[HistoryEntry, None, None]:
        raise NotImplementedError  # pragma: no cover
