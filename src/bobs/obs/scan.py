"""
Module to scan Bitcoin data.
"""
from asyncio import CancelledError, Task
from typing import List, Dict, Any, Callable

from aiohttp import ClientConnectionError, ClientResponseError
from bobs.obs.generators import Tx, iterate_blocks, iterate_mem_txs, iter_filter_block_txs
from bobs.network.rest import RestClient
from bobs.obs.filters import TxFilter
from bobs.obs.obs_utils import print_error, parse_start_and_end
from tqdm.asyncio import tqdm


async def scan_blocks(start: int,
                      end: int,
                      rest: RestClient,
                      settings: Dict[str, Any],
                      *filters: TxFilter) -> List[Tx]:
    """
    Scan from `start` block height to `end` block height, included,
    and yield each transaction from those blocks that match the given criteria.

    See `parse_start_and_end` function for valid `start` and `end` values.
    """
    result: List[Tx] = []
    pending: set[Task] = set()
    result_extend: Callable = result.extend
    try:
        chain_info = await rest.get_chain_info()
        start, end = parse_start_and_end(start, end, chain_info, settings['scan']['force'])
        print(f'Requested scan from block {start} to block {end}, included.\n')
        async for block_done, pending in tqdm(iterate_blocks(start, end, rest,
                                                             settings['limits']['memory_limit'],
                                                             settings['limits']['concurrency_limit']),

                                              miniters=1,
                                              mininterval=0.5,
                                              total=end + 1 - start):
            result_extend(iter_filter_block_txs(await block_done,
                                                settings['filtering']['match_all'],
                                                filters))
    except CancelledError as err:
        # logger.warning('Tasks canceled', exc_info=True)
        print_error('Task canceled', str(err))
    except ClientConnectionError:
        # logger.error('Connection error', exc_info=True)
        print_error('Connection error', 'Cannot establish connection with Bitcoin full node')
    except MemoryError as err:
        # logger.warning('MemoryError', exc_info=True)
        print_error('Memory error', str(err))
    except KeyboardInterrupt:
        print_error('Keyboard Interrupt', 'Stopping execution')
    except Exception as err:
        # logger.error('Something went wrong', exc_info=True)
        print_error('Something went wrong', str(err))
    finally:
        # Clean up
        for task in pending:
            task.cancel()
            try:
                await task
            except:
                pass
    return result


async def scan_mem(rest: RestClient,
                   settings: Dict[str, Any],
                   *filters: TxFilter) -> List[Tx]:
    """
    Scan available mempool, for each transaction get the prevout information from the UTXO set
    """
    result: List[Tx] = []
    result_append: Callable = result.append
    pending: set[Task] = set()
    match_policy: Callable = all if settings['filtering']['match_all'] else any
    f_matches: List[Callable] = [f.match for f in filters]
    no_filter: bool = not filters
    print(f'Requested mempool scan\n')
    try:
        mempool: Dict[str, Any] = await rest.get_mempool(True)
        async for tx_done, pending in tqdm(iterate_mem_txs(rest,
                                                           mempool,
                                                           settings['limits']['concurrency_limit']),
                                           miniters=200,
                                           mininterval=0.5,
                                           total=len(mempool)):
            try:
                tx: Tx = await tx_done
            except ClientResponseError:
                continue
            if no_filter:
                result_append(tx)
            elif match_policy(f(tx) for f in f_matches):
                result_append(tx)
    except CancelledError as err:
        # logger.warning('Tasks canceled', exc_info=True)
        print_error('Task canceled', str(err))
    except ClientConnectionError as err:
        print_error('Connection error', 'Cannot establish connection with Bitcoin full node')
        print(str(err))
    except MemoryError as err:
        # logger.warning('MemoryError', exc_info=True)
        print_error('Memory error', str(err))
    except KeyboardInterrupt:
        print_error('Keyboard Interrupt', 'Stopping execution')
    except Exception as err:
        # logger.error('Something went wrong', exc_info=True)
        print_error('Something went wrong', str(err))
    finally:
        # Clean up
        for task in pending:
            task.cancel()
            try:
                await task
            except:
                pass
    return result
