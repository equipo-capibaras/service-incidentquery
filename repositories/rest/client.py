from repositories.client import ClientRepository
from repositories.rest.base import RestBaseRepository

from .util import TokenProvider


class RestClientRepository(ClientRepository, RestBaseRepository):
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        RestBaseRepository.__init__(self, base_url, token_provider)
