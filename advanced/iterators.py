from asyncio import Queue, create_task, as_completed
from typing import Dict, Any, Optional, AsyncIterator, Iterator

try:
    from containers import Tx
    from filters import TxFilter
    from rpc_client import RpcClient
    from obs_utils import check_memory
except ModuleNotFoundError:
    from advanced.containers import Tx
    from advanced.filters import TxFilter
    from advanced.rpc_client import RpcClient
    from advanced.obs_utils import check_memory


async def get_blocks_from_rpc(start: int,
                              end: int,
                              rpc: RpcClient,
                              memory_limit: Optional[int] = None,
                              max_concurrency: int = 15,
                              verbosity: int = 3) -> AsyncIterator[Dict[str, Any]]:
    """
    Yield blocks asynchronously using an RpcClient.
    If a memory limit is passed, force stop the scan if the limit is reached.
    """

    async def get_block() -> Dict[str, Any]:
        """
        Perform a `getblock` JSON-RPC request picking a blockhash from the queue
        """
        block: Dict[str, Any] = await rpc.getblock(await hashes_queue.get(), verbosity)
        if memory_limit:
            check_memory(memory_limit)
        try:
            if block['nextblockhash'] not in first_batch_blockhashes:
                await hashes_queue.put(block['nextblockhash'])
        except KeyError:
            # If we hit the tip of the blockchain, we assume the scan is over.
            pass
        return block

    hashes_queue: Queue = Queue(max_concurrency)
    # Ask first blockhashes in advance, then follow from block['nextblockhash']
    first_batch_blockhashes = []
    hash_tasks = (create_task(rpc.getblockhash(height)) for height in range(start,
                                                                            min(start + max_concurrency, end+1)))
    for result in as_completed(list(hash_tasks)):
        blockhash = await result
        first_batch_blockhashes.append(blockhash)
        await hashes_queue.put(blockhash)
    block_tasks = (create_task(get_block()) for _ in range(start, end + 1))
    for result in as_completed(list(block_tasks)):
        yield await result


def get_txs(block: Dict[str, Any],
            *filters: TxFilter,
            match_all: bool = False) -> Iterator[Tx]:
    """
    Yield Tx objects while consuming a block.
    If at least one filter is provided, yield only Txs matching a filter.
    If `match_all` is set to True, yield only Txs matching **all** the filters.
    """
    if not filters:
        match_all = True
    while block['tx']:
        tx: Tx = Tx(block['tx'].pop(), block['time'], block['height'])
        matches: Iterator[bool] = (f.match(tx) for f in filters)
        if match_all:
            if all(matches):
                yield tx
        else:
            if any(matches):
                yield tx
