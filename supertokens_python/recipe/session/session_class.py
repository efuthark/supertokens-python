"""
Copyright (c) 2021, VRAI Labs and/or its affiliates. All rights reserved.

This software is licensed under the Apache License, Version 2.0 (the
"License") as published by the Apache Software Foundation.

You may not use this file except in compliance with the License. You may
obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from supertokens_python.normalised_url_path import NormalisedURLPath

if TYPE_CHECKING:
    from .recipe_implementation import RecipeImplementation

from . import session_functions
from .exceptions import raise_unauthorised_exception


class Session:
    def __init__(self, recipe_implementation: RecipeImplementation, access_token, session_handle,
                 user_id, jwt_payload):
        self.__recipe_implementation = recipe_implementation
        self.__access_token = access_token
        self.__session_handle = session_handle
        self.jwt_payload = jwt_payload
        self.user_id = user_id
        self.new_access_token_info = None
        self.new_refresh_token_info = None
        self.new_id_refresh_token_info = None
        self.new_anti_csrf_token = None
        self.remove_cookies = False

    async def revoke_session(self) -> None:
        if await session_functions.revoke_session(self.__recipe_implementation, self.__session_handle):
            self.remove_cookies = True

    async def get_session_data(self) -> dict:
        session_info = await session_functions.get_session_information(self.__recipe_implementation, self.__session_handle)
        return session_info['sessionData']

    async def update_session_data(self, new_session_data) -> None:
        return await session_functions.update_session_data(self.__recipe_implementation, self.__session_handle, new_session_data)

    async def update_jwt_payload(self, new_jwt_payload) -> None:
        result = await self.__recipe_implementation.querier.send_post_request(NormalisedURLPath('/recipe/session'
                                                                                                '/regenerate'), {
            'accessToken': self.__access_token,
            'userDataInJWT': new_jwt_payload
        })
        if result['status'] == 'UNAUTHORISED':
            raise_unauthorised_exception(result['message'])
        self.jwt_payload = result['session']['userDataInJWT']
        if 'accessToken' in result and result['accessToken'] is not None:
            self.__access_token = result['accessToken']['token']
            self.new_access_token_info = result['accessToken']

    def get_user_id(self) -> str:
        return self.user_id

    def get_jwt_payload(self) -> dict:
        return self.jwt_payload

    def get_handle(self) -> str:
        return self.__session_handle

    def get_access_token(self) -> str:
        return self.__access_token

    def __getitem__(self, item):
        return getattr(self, item)