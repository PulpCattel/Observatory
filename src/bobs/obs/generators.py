"""
Generators that get, filter, and yield Bitcoin data
"""

from asyncio import create_task, Task, Semaphore, wait, FIRST_COMPLETED, gather
from typing import Dict, Any, Optional, AsyncGenerator, Tuple, Generator, Iterable, Union, List, Callable

from bobs.bitcoin.containers import Tx
from bobs.network.rest import RestClient
from bobs.obs.filters import TxFilter
from bobs.obs.obs_utils import check_memory


async def iterate_blocks(start: int,
                         end: int,
                         rest: RestClient,
                         memory_limit: Optional[int] = None,
                         max_concurrency: int = 3,
                         no_details: bool = False) -> AsyncGenerator[Tuple[Task, set[Task]], Any]:
    """
    Yields tasks, when awaited, those tasks will return a block dictionary as returned by the REST API or an exception.

    >>> async with RestClient() as rest:
    >>>     async for block_done, _ in iterate_blocks(707296, 707305, rest):
    >>>         print((await block_done)['height'])
    """

    async def get_block(height: int) -> Dict[str, Any]:
        """
        Perform a `get_blockhash` request followed by `get_block`.
        There does not seem to be any overhead from the extra REST call compared to
        following from `nextblockhash`, and this is much cleaner.
        """
        async with sem:
            if memory_limit:
                check_memory(memory_limit)
            return await rest.get_block(await rest.get_blockhash(height), no_details)

    sem = Semaphore(max_concurrency)
    # asyncio.wait does not accept a generator, but it does accept a map
    pending: Union[map, set[Task]] = map(create_task, map(get_block, range(start, end + 1)))
    while pending:
        done, pending = await wait(pending, return_when=FIRST_COMPLETED)
        for block_done in done:
            yield block_done, pending


def iterate_block_txs(block: Dict[str, Any]) -> Generator[Tx, None, None]:
    """
    Yield Tx objects for each transaction in the given block
    """
    time = block['time']
    height = block['height']
    for tx in block['tx']:
        yield Tx(tx, time, height)


def iter_filter_block_txs(block: Dict[str, Any],
                          match_all: bool,
                          filters: Iterable[TxFilter]) -> Generator[Tx, None, None]:
    """
    Similar to `iterate_block_txs` but additionally filters the Tx object using
    given filters.
    """
    match_policy: Callable = all if match_all else any
    f_matches: List[Callable] = [f.match for f in filters]
    no_filter: bool = not filters
    for tx in iterate_block_txs(block):
        if no_filter:
            yield tx
        elif match_policy(f(tx) for f in f_matches):
            yield tx


async def iterate_mem_txs(rest: RestClient,
                          mempool: Dict[str, Any],
                          max_concurrency: int = 3) -> AsyncGenerator[Tuple[Task, set[Task]], Any]:
    """
    Yield a Tx object for each mempool transaction, get prevout information from
    UTXO set.
    """

    async def get_full_tx(txid: str) -> Tx:
        """
        Given an incomplete mempool transaction, asynchronously calls get_utxos/get_tx to
        get prevout information for each transaction input.
        """

        async def update_inputs(tx_input: Dict) -> None:
            utxos: List[Dict[str, Any]] = (await rest.get_utxos(f"{tx_input['txid']}-{tx_input['vout']}"))['utxos']
            if not utxos:
                # It's spending from another mempool transaction
                utxo: Dict[str, Any] = (await rest.get_tx(tx_input['txid']))['vout'][tx_input['vout']]
                # No height
                utxo['height'] = 0
            else:
                utxo = utxos[0]
            tx_input['prevout'] = utxo

        async with sem:
            tx_ = await rest.get_tx(txid)
            await gather(*map(update_inputs, tx_['vin']))
            return Tx(tx_, height=0, date=0)

    sem = Semaphore(max_concurrency)
    # asyncio.wait does not accept a generator, but it does accept a map
    pending = map(create_task, map(get_full_tx, mempool.keys()))
    while pending:
        done, pending = await wait(pending, return_when=FIRST_COMPLETED)
        for tx_done in done:
            yield tx_done, pending
