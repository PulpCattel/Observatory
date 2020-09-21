import inspect
import logging
import os
import sys

import aiohttp
import pytest

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import rpc_client


@pytest.mark.asyncio
async def test_get_client():
    # Default
    client = await rpc_client.RpcClient.get_client()
    assert client.id == 0
    assert isinstance(client.session, aiohttp.ClientSession)
    assert client.endpoint == 'http://127.0.0.1:8332/'
    assert client.whitelisted_methods == []
    await client.close()
    # Custom
    client = await rpc_client.RpcClient.get_client(session='My session', endpoint='My endpoint')
    assert client.id == 0
    assert client.session == 'My session'
    assert client.endpoint == 'My endpoint'
    assert client.whitelisted_methods == []
    return


@pytest.mark.asyncio
async def test_add_methods():
    client = await rpc_client.RpcClient.get_client()
    client.add_methods('My method')
    assert client.whitelisted_methods == ['My method']
    # Check it does not create duplicates
    client.add_methods('My method')
    assert client.whitelisted_methods == ['My method']
    client.add_methods('My method 2')
    assert client.whitelisted_methods == ['My method', 'My method 2']
    client.add_methods('foo', 'bar')
    assert client.whitelisted_methods == ['My method', 'My method 2', 'foo', 'bar']
    await client.close()
    return


@pytest.mark.asyncio
async def test_remove_methods():
    client = await rpc_client.RpcClient.get_client()
    client.remove_methods('My method')
    assert client.whitelisted_methods == []
    client.add_methods('My method')
    client.remove_methods('My method')
    assert client.whitelisted_methods == []
    client.add_methods('Foo', 'Bar')
    client.remove_methods('Foo', 'Bar')
    assert client.whitelisted_methods == []
    client.add_methods('Foo', 'Bar')
    client.remove_methods('Foo')
    assert client.whitelisted_methods == ['Bar']
    await client.close()
    return


@pytest.mark.asyncio
async def test_get_invalid_method():
    client = await rpc_client.RpcClient.get_client()
    with pytest.raises(rpc_client.ForbiddenMethod):
        client.random_method()
