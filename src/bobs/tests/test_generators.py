from copy import deepcopy

from bobs.bitcoin.containers import Tx
from bobs.obs.generators import iterate_blocks, iterate_block_txs
from bobs.obs.obs_utils import parse_start_and_end
from pytest import mark


@mark.require_rest
@mark.asyncio
async def test_iterate_blocks(init_rest):
    info = await init_rest.get_chain_info()
    start, end = parse_start_and_end(-10, 0, info, True)
    async for block_done, _ in iterate_blocks(start, end, init_rest):
        assert (await block_done)['height'] in range(start, end + 1)


@mark.require_rest
@mark.asyncio
async def test_iterate_block_txs(init_rest):
    info = await init_rest.get_chain_info()
    block = await init_rest.get_block(info['bestblockhash'])
    for tx in iterate_block_txs(deepcopy(block)):
        assert isinstance(tx, Tx)
        assert tx.height == block['height']
        assert tx.timestamp_date == block['time']
    assert len(block['tx']) == len(list(iterate_block_txs(block)))
