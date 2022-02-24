"""
Basic tests for the Rest object
"""
# pylint: disable=protected-access # Needed for testing
from aiohttp import ClientSession
from bobs.network.rest import Rest, RestApi, ReqType
from pytest import mark


def test_values() -> None:
    """
    Test RestApi values match Bitcoin Core one.
    https://github.com/bitcoin/bitcoin/blob/master/doc/REST-interface.md
    """
    assert RestApi.TX.value == '/tx'
    assert RestApi.BLOCK.value == '/block'
    assert RestApi.HEADERS.value == '/headers'
    assert RestApi.BLOCKHASH.value == '/blockhashbyheight'
    assert RestApi.CHAININFO.value == '/chaininfo'
    assert RestApi.UTXO.value == '/getutxos'
    assert RestApi.UTXO_CHECK_MEMPOOL.value == '/getutxos/checkmempool'
    assert RestApi.MEMPOOL_INFO.value == '/mempool/info'
    assert RestApi.MEMPOOL_CONTENT.value == '/mempool/contents'


def test_to_uri() -> None:
    """
    Test RestApi method correctly builds URI string.
    """
    assert RestApi.TX.to_uri(ReqType.JSON) == '/tx.json'
    assert RestApi.TX.to_uri(ReqType.JSON, 'txid') == '/tx/txid.json'
    assert RestApi.TX.to_uri(ReqType.JSON, 'txid1', 'txid2') == '/tx/txid1/txid2.json'
    assert RestApi.TX.to_uri(ReqType.HEX, 'txid') == '/tx/txid.hex'


@mark.asyncio
async def test_init(uninit_rest: Rest) -> None:
    """
    Test default Rest object initialization
    """
    # By default it should use the same as Bitcoin Core default.
    assert uninit_rest._endpoint == 'http://127.0.0.1:8332'
    # An AioHttp ClientSession object should be created by default
    assert isinstance(uninit_rest._session, ClientSession)
    # It should support initialization with a custom ClientSession object and endpoint too
    fake_session = ClientSession()
    watermark = 'This is a totally fake session'
    fake_session.id = watermark
    async with Rest(fake_session, 'my endpoint') as rest:
        assert rest._endpoint == 'my endpoint'
        assert rest._session.id == watermark


@mark.asyncio
async def test_get_uri(uninit_rest: Rest) -> None:
    assert uninit_rest.get_uri(RestApi.TX) == 'http://127.0.0.1:8332/rest/tx.json'
    assert uninit_rest.get_uri(RestApi.TX, 'txid') == 'http://127.0.0.1:8332/rest/tx/txid.json'
    assert uninit_rest.get_uri(RestApi.TX, 'txid1', 'txid2') == 'http://127.0.0.1:8332/rest/tx/txid1/txid2.json'
