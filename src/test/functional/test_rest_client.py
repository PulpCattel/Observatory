"""
Test the Rest client object against a real Bitcoin Core REST interface.
For now only testing the REST APIs we use, TODO: cover all.
"""
# Use standard json and not orjson for compatibility testing
from json import loads
from typing import List

from aiohttp import ClientResponse, ClientResponseError
from bobs.network.rest import RestApi, Rest
from bobs.types import Json
from pytest import mark


@mark.require_rest
@mark.functional
@mark.asyncio
async def test_get_response(init_rest: Rest) -> None:
    """
    Do a complete run of all the available RestApi using the base get method, which return a
    AioHttp Response object.
    """
    info_response = await init_rest.get_response(RestApi.CHAININFO)
    assert isinstance(info_response, ClientResponse)
    # Check what we requested.
    assert info_response.headers['Content-Type'] == 'application/json'
    assert str(info_response.url) == init_rest.get_uri(RestApi.CHAININFO)
    info = await info_response.json(encoding='UTF-8')
    assert isinstance(info, dict)

    # Check we are on mainnet, other tests will depend on this
    assert info['chain'] == 'main'
    # Check we are up to date
    assert info['initialblockdownload'] is False
    assert info['blocks'] == info['headers']

    # Get the last block
    block_response = await init_rest.get_response(RestApi.BLOCK_NO_DETAILS, info['bestblockhash'])
    block = await block_response.json(encoding='UTF-8')
    # Check we got the block we asked
    assert block['hash'] == info['bestblockhash']
    assert block['height'] == info['blocks']
    # Check it indeed does not include transaction but just TXIDs.
    assert all(isinstance(tx, str) for tx in block['tx'])
    # Get the previous block hash from the block
    previous_hash = block['previousblockhash']

    # Get the previous block, this time with details
    block_response = await init_rest.get_response(RestApi.BLOCK, previous_hash)
    block = await block_response.json(encoding='UTF-8')
    # Check it's indeed the previous block
    assert block['hash'] == previous_hash
    assert block['height'] == info['blocks'] - 1
    # Check it includes transactions and that those transactions have prevout field.
    # We also check that the first transaction is a coinbase
    txs: List[Json] = block['tx']
    assert 'coinbase' in txs.pop(0)['vin'][0]
    for mem_tx in txs[:100]:
        assert isinstance(mem_tx, dict)
        assert all('prevout' in tx_input for tx_input in mem_tx['vin'])

    # Get block hash of the same block
    hash_response = await init_rest.get_response(RestApi.BLOCKHASH, block['height'])
    blockhash = await hash_response.json(encoding='UTF-8')
    assert blockhash['blockhash'] == block['hash']

    # Get the mempool info
    mempool_response = await init_rest.get_response(RestApi.MEMPOOL_INFO)
    mempool = await mempool_response.json(encoding='UTF-8')
    assert 'size' in mempool
    assert 'maxmempool' in mempool
    assert 'usage' in mempool

    # Get the mempool transaction content
    mempool_response = await init_rest.get_response(RestApi.MEMPOOL_CONTENT)
    mempool = await mempool_response.json(encoding='UTF-8')
    count = 0
    for txid, mem_tx in mempool.items():
        if count >= 100:
            break
        count += 1
        assert isinstance(txid, str)
        assert isinstance(mem_tx, dict)
        # This could throw 404 if the transaction is popped out of the mempool,
        # if that happens we continue with the next TXID
        try:
            # Get the mempool transaction
            tx_response = await init_rest.get_response(RestApi.TX, txid)
        except ClientResponseError:
            # TODO: add logging to check they do not all throw
            continue
        tx = await tx_response.json(encoding='UTF-8')
        # Check that the info in the mempool transaction match the info
        # from the TX REST API
        assert tx['txid'] == txid
        assert tx['weight'] == mem_tx['weight']
        # Get the inputs from each mempool transaction and try to get them from
        # UTXO API.
        for tx_input in tx['vin']:
            utxos_response = await init_rest.get_response(RestApi.UTXO, f"{tx_input['txid']}-{tx_input['vout']}")
            utxos = await utxos_response.json(encoding='UTF-8')
            assert 'utxos' in utxos
            utxos = utxos['utxos']
            # It might be spending from another mempool transaction,
            # in that case we continue and try with the next one.
            if not utxos:
                # TODO: add logging
                continue
            assert 'scriptPubKey' in utxos[0]
            assert 'height' in utxos[0]
            assert 'value' in utxos[0]


@mark.require_rest
@mark.functional
@mark.asyncio
async def test_getters(init_rest: Rest) -> None:
    """
    Test the 3 getters API of the Rest object all return the same as the raw response method.
    * get_json()
    * get_bytes()
    * get_chunks()
    """
    info_response = await init_rest.get_response(RestApi.CHAININFO)
    info = await info_response.json(encoding='UTF-8')
    # Get the last block
    block_response = await init_rest.get_response(RestApi.BLOCK, info['bestblockhash'])
    # Intentionally use json.loads instead of orjson for compatibility testing
    block = await block_response.json(encoding='UTF-8')

    # Check this block Dict against the result from the 3 getters.
    # First get_json()
    block_json = await init_rest.get_json(RestApi.BLOCK, info['bestblockhash'])
    assert block == block_json
    # get_bytes()
    block_bytes = await init_rest.get_bytes(RestApi.BLOCK, info['bestblockhash'])
    assert block == loads(block_bytes)
    # get_chunks()
    block_chunks = await init_rest.get_chunks(RestApi.BLOCK, info['bestblockhash'])
    assert block == loads(b''.join([chunk async for chunk in block_chunks]))


@mark.require_rest
@mark.functional
@mark.asyncio
async def test_wrappers(init_rest: Rest) -> None:
    """
    Test get_*() wrappers against correspondent get_json().
    Some are too flaky to be testable and we just check they behave as
    expected.
    """
    info = await init_rest.get_info()

    # Check get_blockhash()
    blockhash = (await init_rest.get_json(RestApi.BLOCKHASH, info['blocks']))['blockhash']
    assert blockhash == await init_rest.get_blockhash(info['blocks'])

    # Check get_block()
    block = await init_rest.get_json(RestApi.BLOCK_NO_DETAILS, blockhash)
    assert block == await init_rest.get_block(blockhash, True)
    block = await init_rest.get_json(RestApi.BLOCK, blockhash)
    assert block == await init_rest.get_block(blockhash)

    # Check get_mempool()
    mempool = await init_rest.get_mempool()
    assert isinstance(mempool, dict)
    assert 'size' in mempool
    assert 'maxmempool' in mempool
    assert 'usage' in mempool
    mempool_content = await init_rest.get_mempool(True)
    count = 0
    for txid in mempool_content.keys():
        if count >= 100:
            break
        count += 1
        # This could throw 404 if the transaction is popped out of the mempool,
        # if that happens we continue with the next txid
        try:
            assert await init_rest.get_tx(txid) == await init_rest.get_json(RestApi.TX, txid)
        except ClientResponseError:
            # TODO: add logging
            continue

    # Check get_utxos()
    # We use the outpoint of the block reward of the 2nd Bitcoin block,
    # it's unspent since 2009 and it should be quite stable :)
    outpoint = '0e3e2357e806b6cdb1f70b54c3a3a17b6714ee1f0e68bebb44a74b1efd512098-0'
    assert await init_rest.get_utxos(outpoint) == await init_rest.get_json(RestApi.UTXO, outpoint)
    utxo = await init_rest.get_json(RestApi.UTXO_CHECK_MEMPOOL, outpoint)
    assert await init_rest.get_utxos(outpoint, check_mempool=True) == utxo
