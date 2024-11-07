from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, cast

from dependency_injector.wiring import Provide
from flask import Blueprint, Response, request
from flask.views import MethodView

from containers import Container
from models import HistoryEntry, Incident, User
from repositories import EmployeeRepository, IncidentRepository, UserRepository
from repositories.client import ClientRepository

from .util import class_route, error_response, is_valid_uuid4, json_response, requires_token

blp = Blueprint('Incidents', __name__)


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

    def incident_to_dict(self, incident: Incident) -> dict[str, Any]:
        return {
            'id': incident.id,
            'name': incident.name,
            'channel': incident.channel,
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
            incident_dict['history'] = [history_to_dict(x) for x in history]
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


@class_route(blp, '/api/v1/incidents/<incident_id>')
class IncidentDetail(MethodView):
    init_every_request = False

    def incident_to_dict(
        self,
        incident: Incident,
        history: list[HistoryEntry],
        user_repo: UserRepository = Provide[Container.user_repo],
        employee_repo: EmployeeRepository = Provide[Container.employee_repo],
    ) -> dict[str, Any]:
        user_reported_by = user_repo.get(incident.reported_by, incident.client_id)

        if user_reported_by is None:
            raise ValueError(f'User {incident.reported_by} not found')

        user_created_by = user_repo.get(incident.created_by, incident.client_id) or employee_repo.get(
            incident.created_by, incident.client_id
        )

        if user_created_by is None:
            raise ValueError(f'User/Employee {incident.created_by} not found')

        employee_assigned_to = employee_repo.get(incident.assigned_to, incident.client_id)

        if employee_assigned_to is None:
            raise ValueError(f'Employee {incident.assigned_to} not found')

        return {
            'id': incident.id,
            'name': incident.name,
            'channel': incident.channel,
            'reportedBy': {
                'id': user_reported_by.id,
                'name': user_reported_by.name,
                'email': user_reported_by.email,
                'role': 'user',
            },
            'createdBy': {
                'id': user_created_by.id,
                'name': user_created_by.name,
                'email': user_created_by.email,
                'role': 'user' if isinstance(user_created_by, User) else user_created_by.role,
            },
            'assignedTo': {
                'id': employee_assigned_to.id,
                'name': employee_assigned_to.name,
                'email': employee_assigned_to.email,
                'role': employee_assigned_to.role,
            },
            'history': [history_to_dict(x) for x in history],
        }

    @requires_token
    def get(
        self,
        incident_id: str,
        token: dict[str, Any],
        incident_repo: IncidentRepository = Provide[Container.incident_repo],
    ) -> Response:
        if not is_valid_uuid4(incident_id):
            return error_response('Invalid incident ID.', 400)

        incident = incident_repo.get(client_id=token['cid'], incident_id=incident_id)
        if incident is None:
            return error_response('Incident not found.', 404)

        history = incident_repo.get_history(client_id=token['cid'], incident_id=incident_id)

        return json_response(self.incident_to_dict(incident, list(history)), 200)


@class_route(blp, '/api/v1/clients/<client_id>/incidents')
class IncidentsByClient(MethodView):
    init_every_request = False

    def get(
        self,
        client_id: str,
        client_repo: ClientRepository = Provide[Container.client_repo],
    ) -> Response:
        client = client_repo.get(client_id)
        if client is None:
            return error_response('Client not found.', 404)

        return json_response({'status': 'Ok', 'code': 200}, 200)
