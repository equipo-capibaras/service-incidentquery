from typing import Any

from dependency_injector.wiring import Provide
from flask import Blueprint, Response
from flask.views import MethodView

import demo
from containers import Container
from models import HistoryEntry, Incident
from repositories import IncidentRepository, UserRepository

from .util import class_route, json_response, requires_token

blp = Blueprint('Incidents', __name__)


@class_route(blp, '/api/v1/users/me/incidents')
class UserIncidents(MethodView):
    init_every_request = False

    def incident_to_dict(self, incident: Incident) -> dict[str, Any]:
        return {
            'id': incident.id,
            'name': incident.name,
            'channel': incident.channel,
        }

    def history_to_dict(self, entry: HistoryEntry) -> dict[str, Any]:
        return {
            'seq': entry.seq,
            'date': entry.date.isoformat().replace('+00:00', 'Z'),
            'action': entry.action,
            'description': entry.description,
        }

    @requires_token
    def get(
        self,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        incidents = incident_repo.get_all_by_reporter(
            client_id=token['cid'],
            reporter_id=token['sub'],
        )

        resp: list[dict[str, Any]] = []
        for incident in incidents:
            incident_dict = self.incident_to_dict(incident)
            history = incident_repo.get_history(client_id=incident.client_id, incident_id=incident.id)
            incident_dict['history'] = [self.history_to_dict(x) for x in history]
            resp.append(incident_dict)

        return json_response(resp, 200)


@class_route(blp, '/api/v1/employees/me/incidents')
class EmployeeIncidents(MethodView):
    init_every_request = False

    def incident_to_dict(
        self,
        incident: Incident,
        history: list[HistoryEntry],
        user_repo: UserRepository = Provide[Container.user_repo],
    ) -> dict[str, Any]:
        user_reported_by = user_repo.get(incident.reported_by, incident.client_id)

        if user_reported_by is None:
            raise ValueError(f'User {incident.reported_by} not found')

        return {
            'id': incident.id,
            'name': incident.name,
            'reportedBy': {
                'id': user_reported_by.id,
                'name': user_reported_by.name,
                'email': user_reported_by.email,
            },
            'filingDate': history[0].date.isoformat().replace('+00:00', 'Z'),
            'status': history[-1].action,
        }

    def get(self) -> Response:
        data = {
            'incidents': [
                self.incident_to_dict(demo.incident3, demo.incident3_history),
                self.incident_to_dict(demo.incident2, demo.incident2_history),
                self.incident_to_dict(demo.incident1, demo.incident1_history),
            ],
            'totalPages': 1,
            'currentPage': 1,
            'totalIncidents': 3,
        }

        return json_response(data, 200)
