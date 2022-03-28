"""
Run all the targets and additionally check the handling of multiprocessing.Process
"""

# pylint: disable=protected-access
from os import getppid, getpid
from queue import Empty
from sys import byteorder
from time import sleep
from typing import Set

from bobs.network.rest import Rest
from bobs.obs.candidates import Block, BlockV3, TransactionV3, MempoolTx, MempoolTxV2, MempoolTxV3
from bobs.obs.targets import Target, Blocks, BlocksV3, BlockTxsV3, MempoolTxs, MempoolTxsV2, MempoolTxsV3
from bobs.obs.utils import parse_start_and_end
from bobs.types import Toml
from psutil import pid_exists
from pytest import mark, raises


@mark.functional
def test_multiprocess() -> None:
    class FakeTarget(Target):

        async def _worker(self) -> None:
            """
            Dumb worker, it sends out the ID of the processes and then
            it just waits.
            """
            self._result_queue.put_nowait(getpid().to_bytes(8, byteorder=byteorder))
            self._result_queue.put_nowait(getppid().to_bytes(8, byteorder=byteorder))
            sleep(999)

    with FakeTarget('') as target:
        # The process should've automatically started in the background
        assert target._gatherer.is_alive()
        gatherer_pid = int.from_bytes(target._result_queue.get(), byteorder=byteorder)
        our_pid = int.from_bytes(target._result_queue.get(), byteorder=byteorder)
        with raises(Empty):
            # Check nothing else in the Queue
            target._result_queue.get(block=False)
        # Check we are indeed using a different process
        assert gatherer_pid != our_pid
        assert gatherer_pid == target._gatherer.pid
        assert our_pid == getpid()
        assert pid_exists(gatherer_pid)
    # The context manager should've automatically stopped the process.
    # Make sure there are no zombies.
    assert not target._gatherer.is_alive()
    assert target._gatherer.exitcode is not None
    assert not pid_exists(gatherer_pid)


@mark.require_rest
@mark.functional
@mark.asyncio
async def test_blocks(init_rest: Rest, settings: Toml) -> None:
    chain_info = await init_rest.get_info()
    start, end = parse_start_and_end(-10, 0, chain_info, True)
    valid_range = list(range(start, end + 1))
    heights: Set[int] = set()
    with Blocks(settings['network']['endpoint'], start, end) as target:
        for block in target.candidates:
            assert isinstance(block, Block)
            # They are not necessarily in order, but they have to be
            # in the giving range and each of them should appear exactly once
            assert block['height'] in valid_range
            heights.add(block['height'])
    assert len(heights) == 10


@mark.require_rest
@mark.functional
@mark.asyncio
async def test_blocksv3(init_rest: Rest, settings: Toml) -> None:
    chain_info = await init_rest.get_info()
    start, end = parse_start_and_end(-10, 0, chain_info, True)
    valid_range = list(range(start, end + 1))
    heights: Set[int] = set()
    with BlocksV3(settings['network']['endpoint'], start, end) as target:
        for block in target.candidates:
            assert isinstance(block, BlockV3)
            # They are not necessarily in order, but they have to be
            # in the giving range and each of them should appear exactly once
            assert block['height'] in valid_range
            heights.add(block['height'])
            for i, tx in enumerate(block.txs):
                # Test a sample of the transactions, they all have to include
                # the prevout field in the inputs.
                if i > 10:
                    break
                if tx.is_coinbase:
                    continue
                for tx_input in tx['vin']:
                    assert 'prevout' in tx_input
    assert len(heights) == 10


@mark.require_rest
@mark.functional
@mark.asyncio
async def test_block_txsv3(init_rest: Rest, settings: Toml) -> None:
    chain_info = await init_rest.get_info()
    start, end = parse_start_and_end(-5, 0, chain_info, True)
    valid_range = list(range(start, end + 1))
    heights: Set[int] = set()
    with BlockTxsV3(settings['network']['endpoint'], start, end) as target:
        for tx in target.candidates:
            assert isinstance(tx, TransactionV3)
            # They are not necessarily in order, but they have to be
            # in the giving range and each of them should appear exactly once
            assert tx['height'] in valid_range
            heights.add(tx['height'])
    assert len(heights) == 5


@mark.functional
@mark.asyncio
async def test_mempool_txs(settings: Toml) -> None:
    with MempoolTxs(settings['network']['endpoint']) as target:
        for i, tx in enumerate(target.candidates):
            if i > 10:
                break
            assert isinstance(tx, MempoolTx)


@mark.functional
@mark.asyncio
async def test_mempool_txsv2(settings: Toml) -> None:
    with MempoolTxsV2(settings['network']['endpoint']) as target:
        for i, tx in enumerate(target.candidates):
            if i > 10:
                break
            assert isinstance(tx, MempoolTxV2)


@mark.functional
@mark.asyncio
async def test_mempool_txsv3(settings: Toml) -> None:
    with MempoolTxsV3(settings['network']['endpoint']) as target:
        for i, tx in enumerate(target.candidates):
            if i > 10:
                break
            assert isinstance(tx, MempoolTxV3)
