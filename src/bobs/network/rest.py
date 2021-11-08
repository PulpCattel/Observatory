"""
Module to interact with Bitcoin Core REST server
https://github.com/bitcoin/bitcoin/blob/master/doc/REST-interface.md
"""

from asyncio import sleep
from enum import Enum
from typing import Optional, Dict, Any

from aiohttp import ClientSession, ClientTimeout
from orjson import loads

HEADERS = {'User-Agent': 'bobs',
           'content-type': 'text/plain'}
TIMEOUT = 15


class RestMethod(Enum):
    """
    Bitcoin Core supported REST method
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

    def to_path(self, *args) -> str:
        """
        Return complete path for RestMethod
        """
        return f"{self.value}{''.join(f'/{arg}' for arg in args)}.json"


class RestClient:
    """
    Client object to interact with REST server.
    """

    __slots__ = ('session', 'endpoint')

    def __init__(self,
                 session: Optional[ClientSession] = None,
                 endpoint: str = 'http://127.0.0.1:8332',
                 **kwargs):
        """
        Initialize asynchronous REST client, if no session is provided,
        aiohttp.ClientSession() is used. If no `endpoint` is provided,
        Bitcoin Core default one is used. Kwargs argument will be passed
        to aiohttp.ClientSession().
        Can be used with async context manager to cleanly close the session.
        """
        self.session = session if session else ClientSession(headers=HEADERS,
                                                             timeout=ClientTimeout(total=TIMEOUT),
                                                             **kwargs)
        self.endpoint = endpoint

    async def __aenter__(self) -> 'RestClient':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _get_url(self, method: RestMethod, *args) -> str:
        """
        Take a RestMethod and return complete URL string for GET request.
        """
        return f'{self.endpoint}/rest{method.to_path(*args)}'

    async def _get(self, method: RestMethod, *args) -> Dict:
        """
        Perform GET request and return response converted to JSON dict.
        """
        async with self.session.get(self._get_url(method, *args)) as response:
            # Check response HTTP status code
            response.raise_for_status()
            return await response.json(loads=loads)

    async def get_tx(self, txid: str) -> Dict:
        """
        Wrapper around Tx method
        """
        return await self._get(RestMethod.TX, txid)

    async def get_block(self, blockhash: str, no_details: bool = False) -> Dict[str, Any]:
        """
        Wrapper around Block or BlockNoDetails method
        """
        method = RestMethod.BLOCK_NO_DETAILS if no_details else RestMethod.BLOCK
        return await self._get(method, blockhash)

    async def get_blockhash(self, height: int) -> str:
        """
        Wrapper around Blockhash method
        """
        return (await self._get(RestMethod.BLOCKHASH, height))['blockhash']

    async def get_chain_info(self) -> Dict:
        """
        Wrapper around Chaininfo method
        """
        return await self._get(RestMethod.CHAININFO)

    async def get_headers(self, count: int, blockhash: str) -> Dict:
        """
        Wrapper around Headers method
        """
        return await self._get(RestMethod.HEADERS, count, blockhash)

    async def get_utxos(self, *outpoints, check_mempool: bool = False) -> Dict:
        """
        Wrapper around Utxo and UtxoCheckMempool
        """
        method = RestMethod.UTXO_CHECK_MEMPOOL if check_mempool else RestMethod.UTXO
        return await self._get(method, *outpoints)

    async def get_mempool(self, include_txs: bool = False) -> Dict:
        """
        Wrapper around MempoolInfo and MempoolContent
        """
        method = RestMethod.MEMPOOL_CONTENT if include_txs else RestMethod.MEMPOOL_INFO
        return await self._get(method)

    async def close(self) -> None:
        """
        Close the async session and wait for graceful shutdown
        https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        """
        await self.session.close()
        await sleep(0.1)
