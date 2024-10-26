from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration

from repositories.rest import RestUserRepository


class Container(DeclarativeContainer):
    wiring_config = WiringConfiguration(packages=['blueprints'])
    config = providers.Configuration()

    user_repo = providers.ThreadSafeSingleton(
        RestUserRepository,
        base_url=config.svc.user.url,
        token_provider=config.svc.user.token_provider,
    )
