import asyncio

import aiohttp


class RpcError(Exception):
    pass


class ForbiddenMethod(RpcError):
    pass


class RpcClient:
    """
    Client object to interact with RPC server.
    Methods that are not whitelisted will raise a ForbiddenMethod exception.
    """

    def __init__(self, session, endpoint):
        self.session = session
        self.endpoint = endpoint
        self.id = 0
        self.__whitelisted_methods = []
        return

    def __getattr__(self, method):
        if method not in self.__whitelisted_methods:
            error_msg = f'Invalid method: method "{method}" is not whitelisted'
            raise ForbiddenMethod(error_msg)

        async def call(*params):
            payload = {
                'jsonrpc': '2.0',
                'id': self.id,
                'method': method,
                'params': params if params else None
            }
            self.id += 1
            async with self.session.post(self.endpoint, json=payload) as response:
                response.raise_for_status()
                result = (await response.json())['result']
            return result

        return call

    @property
    def whitelisted_methods(self):
        return self.__whitelisted_methods

    def add_methods(self, *methods):
        for method in methods:
            if method in self.__whitelisted_methods:
                continue
            self.__whitelisted_methods.append(method)
        return

    def remove_methods(self, *methods):
        for method in methods:
            if method not in self.__whitelisted_methods:
                continue
            self.__whitelisted_methods.remove(method)
        return

    async def close(self):
        await self.session.close()
        await asyncio.sleep(0.1)
        return

    @classmethod
    async def get_client(cls, session=None, endpoint='', user='', pwd=''):
        if not session:
            session = aiohttp.ClientSession(
                headers={'content-type': 'application/json'},
                auth=aiohttp.BasicAuth(user, pwd),
                timeout=aiohttp.ClientTimeout(total=0)
            )
        if not endpoint:
            endpoint = 'http://127.0.0.1:8332/'
        return cls(session, endpoint)
