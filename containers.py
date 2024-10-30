from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration

from repositories.firestore import FirestoreIncidentRepository
from repositories.rest import RestEmployeeRepository, RestUserRepository


class Container(DeclarativeContainer):
    wiring_config = WiringConfiguration(packages=['blueprints'])
    config = providers.Configuration()

    user_repo = providers.ThreadSafeSingleton(
        RestUserRepository,
        base_url=config.svc.user.url,
        token_provider=config.svc.user.token_provider,
    )

    employee_repo = providers.ThreadSafeSingleton(
        RestEmployeeRepository,
        base_url=config.svc.client.url,
        token_provider=config.svc.client.token_provider,
    )

    incident_repo = providers.ThreadSafeSingleton(FirestoreIncidentRepository, database=config.firestore.database)
