from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, cast

from dependency_injector.wiring import Provide
from flask import Blueprint, Response, request
from flask.views import MethodView

from containers import Container
from models import HistoryEntry, Incident
from repositories import IncidentRepository, UserRepository

from .util import class_route, error_response, json_response, requires_token

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

    @requires_token
    def get(
        self,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        # Optional pagination parameters
        page_size = request.args.get('page_size', default=5, type=int)
        page_number = request.args.get('page_number', default=1, type=int)

        # Validate the value of page_size
        allowed_page_sizes = [5, 10, 20]
        if page_size not in allowed_page_sizes:
            return error_response(f'Invalid page_size. Allowed values are {allowed_page_sizes}.', 400)

        # Validate the value of page_number
        if page_number < 1:
            return error_response('Invalid page_number. Page number must be 1 or greater.', 400)

        total_incidents = incident_repo.count_by_assignee(
            client_id=token['cid'],
            assignee_id=token['sub'],
        )
        total_pages = (total_incidents + page_size - 1) // page_size

        incidents = incident_repo.get_all_by_assignee(
            client_id=token['cid'],
            assignee_id=token['sub'],
            offset=(page_number - 1) * page_size,
            limit=page_size,
        )

        with ThreadPoolExecutor() as executor:
            incidents_futures: list[Future[dict[str, Any]]] = [
                executor.submit(
                    cast(
                        Callable[[Incident], dict[str, Any]],
                        lambda incident: self.incident_to_dict(
                            incident, list(incident_repo.get_history(client_id=token['cid'], incident_id=incident.id))
                        ),
                    ),
                    incident,
                )
                for incident in incidents
            ]

        incidents_dict = [x.result() for x in incidents_futures]

        data = {
            'incidents': incidents_dict,
            'totalPages': total_pages,
            'currentPage': page_number,
            'totalIncidents': total_incidents,
        }

        return json_response(data, 200)
