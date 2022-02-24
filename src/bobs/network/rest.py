"""
Module to interact with Bitcoin Core REST server
https://github.com/bitcoin/bitcoin/blob/master/doc/REST-interface.md
"""
from asyncio import sleep
from enum import Enum
from typing import Optional, AsyncIterator

from aiohttp import ClientSession, ClientTimeout, ClientResponse
from bobs.types import RestUriArg, Json
from orjson import loads

BASE_CURL_ARGS = (
    '--compressed', '--tr-encoding', '-Z', '--parallel-max', '8', '--parallel-immediate', '--raw', '--no-buffer',
    '--fail-early')

HEADERS = {'User-Agent': 'bobs',
           'content-type': 'application/json'}
TIMEOUT = 15


class ReqType(Enum):
    """
    Possible request types of the Rest interface.
    Currently only JSON is used.
    """
    BIN = ".bin"
    HEX = ".hex"
    JSON = ".json"


class RestApi(Enum):
    """
    Bitcoin Core supported REST API.
    """

    # Given a transaction hash, return a transaction.
    # By default, this method will only search the mempool. To query for a confirmed transaction,
    # enable the transaction index via "txindex=1" command line/configuration option.
    TX = '/tx'
    # Given a block hash, return a block
    BLOCK = '/block'
    # Given a block hash, return a block only containing the TXID
    # instead of the complete transaction details
    BLOCK_NO_DETAILS = '/block/notxdetails'
    # Given a count and a block hash, return amount of block headers in upward direction
    HEADERS = '/headers'
    # Given a height, return hash of block at height provided
    BLOCKHASH = '/blockhashbyheight'
    # Return various state info regarding block chain processing
    # ONLY SUPPORTS JSON FORMAT!
    CHAININFO = '/chaininfo'
    # Query UTXO set given a set of outpoints
    UTXO = '/getutxos'
    # Query UTXO set given a set of outpoint and apply mempool transactions during the calculation,
    # thus exposing their UTXOs and removing outputs that they spend
    UTXO_CHECK_MEMPOOL = '/getutxos/checkmempool'
    # Return various information about the mempool
    MEMPOOL_INFO = '/mempool/info'
    # Return transactions in the mempool
    MEMPOOL_CONTENT = '/mempool/contents'

    def to_uri(self, req_type: ReqType, *args: RestUriArg) -> str:
        """
        Return complete URI for RestApi.
        """
        return f"{self.value}{''.join(f'/{arg}' for arg in args)}{req_type.value}"


class Rest:
    """
    Client object to interact with REST server.
    """

    __slots__ = ('_session', '_endpoint')

    def __init__(self,
                 session: Optional[ClientSession] = None,
                 endpoint: str = 'http://127.0.0.1:8332') -> None:
        """
        Initialize asynchronous REST client, if no session is provided,
        aiohttp.ClientSession() is used. If no `endpoint` is provided,
        Bitcoin Core default one is used. Kwargs argument will be passed
        to aiohttp.ClientSession().
        Can be used with async context manager to cleanly close the session.
        """
        self._session = session if session else ClientSession(headers=HEADERS,
                                                              timeout=ClientTimeout(total=TIMEOUT))
        self._endpoint = endpoint

    async def __aenter__(self) -> 'Rest':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # type: ignore[no-untyped-def]
        await self.close()

    @property
    def endpoint(self) -> str:
        return self._endpoint

    def get_uri(self, method: RestApi, *args: RestUriArg) -> str:
        """
        Take a RestApi and return complete URI string for GET request.
        """
        return f'{self._endpoint}/rest{method.to_uri(ReqType.JSON, *args)}'

    async def get_response(self, method: RestApi, *args: RestUriArg) -> ClientResponse:
        """
        Perform GET request and return ClientResponse object.
        """
        response = await self._session.get(self.get_uri(method, *args))
        response.raise_for_status()
        return response

    async def get_json(self, method: RestApi, *args: RestUriArg) -> Json:
        """
        Return the response body converted to Dict.
        """
        json: Json = await (await self.get_response(method, *args)).json(encoding='UTF-8',
                                                                         loads=loads)
        return json

    async def get_bytes(self, method: RestApi, *args: RestUriArg) -> bytes:
        """
        Return the response body in bytes.
        """
        return await (await self.get_response(method, *args)).read()

    async def get_chunks(self, method: RestApi, *args: RestUriArg, chunk_size: int = 0) -> AsyncIterator[bytes]:
        """
        Yield each chunk of bytes of the response body. If `chunk_size` is > 0, that will be used as the size
        of each yielded chunk.
        """
        if chunk_size > 0:
            return (await self.get_response(method, *args)).content.iter_chunked(chunk_size)
        return (await self.get_response(method, *args)).content.iter_any()

    async def get_tx(self, txid: str) -> Json:
        """
        Wrapper around Tx method
        """
        return await self.get_json(RestApi.TX, txid)

    async def get_block(self, blockhash: str, no_details: bool = False) -> Json:
        """
        Wrapper around Block or BlockNoDetails method
        """
        return await self.get_json(RestApi.BLOCK_NO_DETAILS if no_details else RestApi.BLOCK, blockhash)

    async def get_blockhash(self, height: int) -> str:
        """
        Wrapper around Blockhash method
        """
        blockhash: str = (await self.get_json(RestApi.BLOCKHASH, height))['blockhash']
        return blockhash

    async def get_info(self) -> Json:
        """
        Wrapper around Chaininfo method
        """
        return await self.get_json(RestApi.CHAININFO)

    async def get_headers(self, count: int, blockhash: str) -> Json:
        """
        Wrapper around Headers method
        """
        return await self.get_json(RestApi.HEADERS, count, blockhash)

    async def get_utxos(self, *outpoints: str, check_mempool: bool = False) -> Json:
        """
        Wrapper around Utxo and UtxoCheckMempool
        """
        return await self.get_json(RestApi.UTXO_CHECK_MEMPOOL if check_mempool else RestApi.UTXO, *outpoints)

    async def get_mempool(self, include_txs: bool = False) -> Json:
        """
        Wrapper around MempoolInfo and MempoolContent
        """
        return await self.get_json(RestApi.MEMPOOL_CONTENT if include_txs else RestApi.MEMPOOL_INFO)

    async def close(self) -> None:
        """
        Close the async session and wait for graceful shutdown
        https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        """
        await self._session.close()
        await sleep(0.1)
