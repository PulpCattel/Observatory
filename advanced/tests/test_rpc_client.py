from inspect import getfile, currentframe
from os import path
from sys import path as sys_path

from pytest import mark, raises
from aiohttp import ClientSession

# Used to import from parent directories
currentdir = path.dirname(path.abspath(getfile(currentframe())))
parentdir = path.dirname(currentdir)
parent_parent = path.dirname(parentdir)
sys_path.insert(0, parentdir)
sys_path.insert(0, parent_parent)

from rpc_client import RpcClient, ForbiddenMethod
from settings import settings


@mark.asyncio
async def test_get_client():
    # Default
    async with RpcClient() as rpc:
        assert rpc.id == 0
        assert isinstance(rpc.session, ClientSession)
        assert rpc.endpoint == 'http://127.0.0.1:8332/'
        assert rpc.whitelisted_methods == []
    # Custom, no context manager because the session is fake
    rpc = RpcClient(session='My session', endpoint='My endpoint')
    assert rpc.id == 0
    assert rpc.session == 'My session'
    assert rpc.endpoint == 'My endpoint'
    assert rpc.whitelisted_methods == []


@mark.asyncio
async def test_add_methods():
    async with RpcClient() as rpc:
        rpc.add_methods('My method')
        assert rpc.whitelisted_methods == ['My method']
        # Check it does not create duplicates
        rpc.add_methods('My method')
        assert rpc.whitelisted_methods == ['My method']
        rpc.add_methods('My method 2')
        assert rpc.whitelisted_methods == ['My method', 'My method 2']
        rpc.add_methods('foo', 'bar')
        assert rpc.whitelisted_methods == ['My method', 'My method 2', 'foo', 'bar']


@mark.asyncio
async def test_remove_methods():
    async with RpcClient() as rpc:
        rpc.remove_methods('My method')
        assert rpc.whitelisted_methods == []
        rpc.add_methods('My method')
        rpc.remove_methods('My method')
        assert rpc.whitelisted_methods == []
        rpc.add_methods('Foo', 'Bar')
        rpc.remove_methods('Foo', 'Bar')
        assert rpc.whitelisted_methods == []
        rpc.add_methods('Foo', 'Bar')
        rpc.remove_methods('Foo')
        assert rpc.whitelisted_methods == ['Bar']


@mark.asyncio
async def test_get_invalid_method():
    async with RpcClient() as rpc:
        with raises(ForbiddenMethod):
            rpc.random_method()


@mark.asyncio
async def test_build_payload():
    async with RpcClient() as rpc:
        payload = rpc.build_payload('getblock', [1, 2, 3])
        assert payload == {'jsonrpc': '2.0',
                           'id': 0,
                           'method': 'getblock',
                           'params': [1, 2, 3]}
        payload = rpc.build_payload('getblock')
        assert payload == {'jsonrpc': '2.0',
                           'id': 0,
                           'method': 'getblock',
                           'params': None}


@mark.asyncio
async def test_rpc_post():
    async with RpcClient(user=settings['rpc_user'],
                         pwd=settings['rpc_password']) as rpc:
        rpc.add_methods('getblockchaininfo', 'getblockhash')
        info = await rpc.getblockchaininfo()
        assert isinstance(info, dict)
        blockhash = await rpc.getblockhash(info['blocks'])
        assert blockhash == info['bestblockhash']