from inspect import getfile, currentframe
from os import path
from sys import path as sys_path
from copy import deepcopy

from pytest import mark

# Used to import from parent directories
currentdir = path.dirname(path.abspath(getfile(currentframe())))
parentdir = path.dirname(currentdir)
parent_parent = path.dirname(parentdir)
sys_path.insert(0, parentdir)
sys_path.insert(0, parent_parent)

from rpc_client import RpcClient, ForbiddenMethod
from obs_utils import parse_start_and_end
from iterators import get_blocks_from_rpc, get_txs
from settings import settings
from containers import Tx
from filters import CoinbaseFilter


@mark.asyncio
async def test_get_blocks_from_rpc():
    async with RpcClient(user=settings['rpc_user'],
                         pwd=settings['rpc_password']) as rpc:
        rpc.add_methods('getblockchaininfo', 'getblock', 'getblockhash')
        info = await rpc.getblockchaininfo()
        start, end = parse_start_and_end(-20, 0, info, False)
        async for block in get_blocks_from_rpc(start, end, rpc, verbosity=1):
            assert block['height'] in range(start, end+1)
        start, end = parse_start_and_end(-5, 0, info, False)
        async for block in get_blocks_from_rpc(start, end, rpc, verbosity=1):
            assert block['height'] in range(start, end+1)


@mark.asyncio
async def test_get_txs():
    async with RpcClient(user=settings['rpc_user'],
                         pwd=settings['rpc_password']) as rpc:
        rpc.add_methods('getblockchaininfo', 'getblock')
        info = await rpc.getblockchaininfo()
        block = await rpc.getblock(info['bestblockhash'], 3)
        assert len(block['tx']) > 1
        for tx in get_txs(deepcopy(block)):
            assert isinstance(tx, Tx)
            assert tx.height == block['height']
        assert len(block['tx']) == len(list(get_txs(deepcopy(block))))
        assert 1 == len(list(get_txs(deepcopy(block), CoinbaseFilter())))
