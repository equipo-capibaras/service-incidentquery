from typing import Any

from flask import Blueprint, Response
from flask.views import MethodView

import demo
from models import HistoryEntry, Incident

from .util import class_route, json_response

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

    def get(self) -> Response:
        i1 = self.incident_to_dict(demo.incident1)
        i1['history'] = [self.history_to_dict(x) for x in demo.incident1_history]

        i2 = self.incident_to_dict(demo.incident2)
        i2['history'] = [self.history_to_dict(x) for x in demo.incident2_history]

        i3 = self.incident_to_dict(demo.incident3)
        i3['history'] = [self.history_to_dict(x) for x in demo.incident3_history]

        return json_response([i3, i2, i1], 200)


@class_route(blp, '/api/v1/employees/me/incidents')
class EmployeeIncidents(MethodView):
    init_every_request = False

    def incident_to_dict(self, incident: Incident, history: list[HistoryEntry]) -> dict[str, Any]:
        return {
            'id': incident.id,
            'name': incident.name,
            'reportedBy': {
                'id': incident.reported_by,
                'name': 'María Fernanda Gómez',
                'email': 'maria.gomez@example.com',
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
