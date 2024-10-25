from datetime import UTC, datetime
from typing import Any

from flask import Blueprint, Response
from flask.views import MethodView

import demo
from models import HistoryEntry, Incident

from .util import class_route, json_response

blp = Blueprint('Incidents', __name__)


def incident_to_dict(incident: Incident) -> dict[str, Any]:
    return {
        'id': incident.id,
        'name': incident.name,
        'channel': incident.channel,
    }


def history_to_dict(entry: HistoryEntry) -> dict[str, Any]:
    return {
        'seq': entry.seq,
        'date': entry.date.isoformat().replace('+00:00', 'Z'),
        'action': entry.action,
        'description': entry.description,
    }


@class_route(blp, '/api/v1/users/me/incidents')
class UserIncidents(MethodView):
    init_every_request = False

    def get(self) -> Response:
        i1 = incident_to_dict(demo.incident1)
        i1['history'] = [history_to_dict(x) for x in demo.incident1_history]

        i2 = incident_to_dict(demo.incident2)
        i2['history'] = [history_to_dict(x) for x in demo.incident2_history]

        i3 = incident_to_dict(demo.incident3)
        i3['history'] = [history_to_dict(x) for x in demo.incident3_history]

        return json_response([i1, i2, i3], 200)


@class_route(blp, '/api/v1/employees/me/incidents')
class EmployeeIncidents(MethodView):
    init_every_request = False

    def get(self) -> Response:
        data = {
            'incidents': [
                {
                    'id': '8731bb72-0e2a-4887-b6fd-c2c505684472',
                    'name': 'Cobro incorrecto',
                    'user': {
                        'id': 'b713f559-cae5-4db3-992a-d3553fb25000',
                        'name': 'María Fernanda Gómez',
                        'email': 'maria.gomez@example.com',
                    },
                    'filingDate': datetime(2024, 10, 22, 14, 26, 22, tzinfo=UTC).isoformat().replace('+00:00', 'Z'),
                    'status': 'created',
                },
                {
                    'id': '2d607056-e710-46d2-99a8-7a373921b398',
                    'name': 'Retorno pago',
                    'user': {
                        'id': 'b713f559-cae5-4db3-992a-d3553fb25000',
                        'name': 'María Fernanda Gómez',
                        'email': 'maria.gomez@example.com',
                    },
                    'filingDate': datetime(2024, 10, 21, 16, 47, 6, tzinfo=UTC).isoformat().replace('+00:00', 'Z'),
                    'status': 'closed',
                },
                {
                    'id': '5de0cfba-76a8-4721-abfe-45091fb35889',
                    'name': 'Internet pago',
                    'user': {
                        'id': 'b713f559-cae5-4db3-992a-d3553fb25000',
                        'name': 'María Fernanda Gómez',
                        'email': 'maria.gomez@example.com',
                    },
                    'filingDate': datetime(2024, 10, 20, 9, 6, 25, tzinfo=UTC).isoformat().replace('+00:00', 'Z'),
                    'status': 'escalated',
                },
                {
                    'id': '3a7708dd-e419-45dc-9948-451c456f633f',
                    'name': 'Cambio precio servicios',
                    'user': {
                        'id': 'b713f559-cae5-4db3-992a-d3553fb25000',
                        'name': 'María Fernanda Gómez',
                        'email': 'maria.gomez@example.com',
                    },
                    'filingDate': datetime(2024, 10, 19, 22, 56, 31, tzinfo=UTC).isoformat().replace('+00:00', 'Z'),
                    'status': 'closed',
                },
            ],
            'totalPages': 1,
            'currentPage': 1,
            'totalIncidents': 4,
        }

        return json_response(data, 200)
