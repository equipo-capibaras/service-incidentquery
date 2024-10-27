import logging
from typing import Any, cast

import dacite
import requests

from models import User
from repositories import UserRepository

from .util import TokenProvider


class RestUserRepository(UserRepository):
    def __init__(self, base_url: str, token_provider: TokenProvider | None) -> None:
        self.base_url = base_url
        self.token_provider = token_provider
        self.logger = logging.getLogger(self.__class__.__name__)

    def authenticated_get(self, url: str) -> requests.Response:
        if self.token_provider is None:
            headers = None
        else:
            id_token = self.token_provider.get_token()
            headers = {'Authorization': f'Bearer {id_token}'}

        return requests.get(url, timeout=2, headers=headers)

    def get(self, user_id: str, client_id: str) -> User | None:
        resp = self.authenticated_get(f'{self.base_url}/api/v1/users/{client_id}/{user_id}')

        if resp.status_code == requests.codes.ok:
            json = cast(dict[str, Any], resp.json())
            # Convert from json naming convention to Python naming convention
            json['client_id'] = json.pop('clientId')
            return dacite.from_dict(data_class=User, data=json)

        if resp.status_code == requests.codes.not_found:
            return None

        resp.raise_for_status()

        raise requests.HTTPError('Unexpected response from server', response=resp)
