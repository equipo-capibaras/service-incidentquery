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
class HealthCheck(MethodView):
    init_every_request = False

    def get(self) -> Response:
        i1 = incident_to_dict(demo.incident1)
        i1['history'] = [history_to_dict(x) for x in demo.incident1_history]

        i2 = incident_to_dict(demo.incident2)
        i2['history'] = [history_to_dict(x) for x in demo.incident2_history]

        i3 = incident_to_dict(demo.incident3)
        i3['history'] = [history_to_dict(x) for x in demo.incident3_history]

        return json_response([i1, i2, i3], 200)
