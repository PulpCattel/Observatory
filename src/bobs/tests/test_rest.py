"""
Tests for the rest module
"""
from aiohttp import ClientSession, ClientResponseError
from bobs.network.rest import RestClient, RestMethod
from pytest import mark


def test_values():
    """
    Test RestApi values matches Bitcoin Core one.
    https://github.com/bitcoin/bitcoin/blob/master/doc/REST-interface.md
    """
    assert RestMethod.TX.value == '/tx'
    assert RestMethod.BLOCK.value == '/block'
    assert RestMethod.HEADERS.value == '/headers'
    assert RestMethod.BLOCKHASH.value == '/blockhashbyheight'
    assert RestMethod.CHAININFO.value == '/chaininfo'
    assert RestMethod.UTXO.value == '/getutxos'
    assert RestMethod.UTXO_CHECK_MEMPOOL.value == '/getutxos/checkmempool'
    assert RestMethod.MEMPOOL_INFO.value == '/mempool/info'
    assert RestMethod.MEMPOOL_CONTENT.value == '/mempool/contents'


def test_to_path():
    """
    Test to_path() RestApi method
    """
    assert RestMethod.TX.to_path() == '/tx.json'
    assert RestMethod.TX.to_path('txid') == '/tx/txid.json'
    assert RestMethod.TX.to_path('txid1', 'txid2') == '/tx/txid1/txid2.json'


@mark.asyncio
async def test_init(uninit_rest):
    """
    Test RestClient initialization
    """
    assert uninit_rest.endpoint == 'http://127.0.0.1:8332'
    assert isinstance(uninit_rest.session, ClientSession)
    assert uninit_rest.session.raise_for_status is False
    async with RestClient(ClientSession(raise_for_status=True), 'my endpoint') as rest:
        assert rest.endpoint == 'my endpoint'
        assert rest.session.raise_for_status is True


@mark.asyncio
async def test_get_url(uninit_rest):
    """
    Test get_url() RestClient method
    """
    assert uninit_rest._get_url(RestMethod.TX) == 'http://127.0.0.1:8332/rest/tx.json'
    assert uninit_rest._get_url(RestMethod.TX, 'txid') == 'http://127.0.0.1:8332/rest/tx/txid.json'
    assert uninit_rest._get_url(RestMethod.TX, 'txid1', 'txid2') == \
           'http://127.0.0.1:8332/rest/tx/txid1/txid2.json'


"""
These tests require a running and reachable Bitcoin Core node  with the REST server enabled.
"""


@mark.require_rest
@mark.asyncio
async def test_get(init_rest):
    """
    Test _get() RestClient method
    """
    chain_info = await init_rest._get(RestMethod.CHAININFO)
    blockhash = chain_info['bestblockhash']
    height = chain_info['blocks']
    assert (await init_rest._get(RestMethod.BLOCKHASH, height))['blockhash'] == blockhash


@mark.require_rest
@mark.asyncio
async def test_wrappers(init_rest):
    """
    Test each get() wrapper against correspondent _get().
    """
    chain_info = await init_rest._get(RestMethod.CHAININFO)
    blockhash = (await init_rest._get(RestMethod.BLOCKHASH, chain_info['blocks']))['blockhash']
    mempool_content = await init_rest._get(RestMethod.MEMPOOL_CONTENT)
    for key in mempool_content.keys():
        # This could throw 404 if the transaction is popped out of the mempool,
        # if that happens we keep trying with a different txid
        try:
            assert await init_rest.get_tx(key) == await init_rest._get(RestMethod.TX, key)
        except ClientResponseError:
            continue
        break
    assert await init_rest.get_block(blockhash) == await init_rest._get(RestMethod.BLOCK, blockhash)
    block_no_details = await init_rest._get(RestMethod.BLOCK_NO_DETAILS, blockhash)
    assert await init_rest.get_block(blockhash, no_details=True) == block_no_details
    assert await init_rest.get_blockhash(chain_info['blocks']) == blockhash
    # We use the outpoint of the block reward of the 2nd Bitcoin block,
    # it's unspent since 2009 and it should be pretty stable
    outpoint = '0e3e2357e806b6cdb1f70b54c3a3a17b6714ee1f0e68bebb44a74b1efd512098-0'
    assert await init_rest.get_utxos(outpoint) == await init_rest._get(RestMethod.UTXO, outpoint)
    utxo = await init_rest._get(RestMethod.UTXO_CHECK_MEMPOOL, outpoint)
    assert await init_rest.get_utxos(outpoint, check_mempool=True) == utxo


@mark.xfail
@mark.require_rest
@mark.asyncio
async def test_chaininfo_wrapper(init_rest):
    """
    Chaininfo wrapper is tested separately as it is somewhat flaky, it changes all the time
    """
    assert await init_rest.get_chain_info() == await init_rest._get(RestMethod.CHAININFO)


@mark.xfail
@mark.require_rest
@mark.asyncio
async def test_mempool_wrappers(init_rest):
    """
    Mempool wrappers are tested separately as they are somewhat flaky, mempool changes constantly.
    """
    assert await init_rest.get_mempool() == await init_rest._get(RestMethod.MEMPOOL_INFO)
    assert await init_rest.get_mempool(include_txs=True) == await init_rest._get(RestMethod.MEMPOOL_CONTENT)
