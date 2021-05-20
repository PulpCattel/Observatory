from asyncio import sleep
from typing import Optional, Any, List, Callable, Dict

from aiohttp import ClientSession, BasicAuth, ClientTimeout


class RpcError(Exception):
    pass


class ForbiddenMethod(RpcError):
    pass


class RpcClient:
    """
    Client object to interact with RPC server.
    Methods that are not whitelisted will raise a ForbiddenMethod exception.
    """

    def __init__(self,
                 session: Optional[ClientSession] = None,
                 endpoint: Optional[str] = None,
                 user: str = '',
                 pwd: str = '',
                 **kwargs: Any) -> None:
        """
        Initialize asynchronous JSON-RPC client, if no session is provided, aiohttp.ClientSession() is used.
        If no `endpoint` is provided, Bitcoin Core default one is used.
        Kwargs argument will be passed to aiohttp.ClientSession().
        Can be used with async context manager to cleanly close the session.
        """
        self.id: int = 0
        self.__whitelisted_methods: List[str] = []
        if not session:
            self.session: ClientSession = ClientSession(headers={'content-type': 'application/json'},
                                                        auth=BasicAuth(user, pwd),
                                                        timeout=ClientTimeout(total=0),
                                                        **kwargs)
        else:
            self.session = session
        if not endpoint:
            self.endpoint: str = 'http://127.0.0.1:8332/'
        else:
            self.endpoint = endpoint

    async def __aenter__(self) -> 'RpcClient':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def build_payload(self, method: str, params: Optional[Any] = None) -> Dict[str, Any]:
        return {'jsonrpc': '2.0',
                'id': self.id,
                'method': method,
                'params': params}

    def __getattr__(self, method: str) -> Callable:
        if method not in self.__whitelisted_methods:
            error_msg: str = f'Invalid method: method "{method}" is not whitelisted'
            raise ForbiddenMethod(error_msg)

        async def post(*params: Any) -> Any:
            payload: Dict[str, Any] = self.build_payload(method, params)
            self.id += 1
            async with self.session.post(self.endpoint,
                                         json=payload) as response:
                response.raise_for_status()
                return (await response.json())['result']

        return post

    @property
    def whitelisted_methods(self) -> List[str]:
        return self.__whitelisted_methods

    def add_methods(self, *methods: str) -> None:
        for method in methods:
            if method in self.__whitelisted_methods:
                continue
            self.__whitelisted_methods.append(method)

    def remove_methods(self, *methods: str) -> None:
        for method in methods:
            try:
                self.__whitelisted_methods.remove(method)
            except ValueError:
                continue

    async def close(self) -> None:
        await self.session.close()
        await sleep(0.1)
