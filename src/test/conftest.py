"""
Pytest helper classes and fixtures
"""
# pylint: disable=redefined-outer-name
from asyncio import get_event_loop, AbstractEventLoop

import pytest_asyncio
from bobs.network.rest import Rest
from bobs.obs.candidates import Block, BlockV3, Transaction, TransactionV3
from bobs.settings import Settings
from bobs.types import Toml, Json
from data import BLOCK_REST_JSON, BLOCKV3_REST_JSON, TRANSACTION_REST_JSON, CHAIN_INFO_REST_JSON
from pytest import fixture


# Session level fixtures

@fixture(scope='session')
def settings() -> Toml:
    """
    Yield Settings Dict , shared across the entire test session
    """
    return Settings.from_file(force_exist=True)


@fixture(scope="session")
def event_loop() -> AbstractEventLoop:
    """
    Yield asyncio event loop shared across the entire session
    """
    loop = get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def uninit_rest() -> Rest:
    """
    Yield uninitialized REST client shared across the entire test session
    """
    async with Rest() as rest:
        yield rest


@pytest_asyncio.fixture(scope='session')
async def init_rest(settings: Toml) -> Rest:
    """
    Yield REST client initialized from settings configuration file, shared across the entire test session
    """
    async with Rest(endpoint=settings['network']['endpoint']) as rest:
        yield rest


# Function level fixtures

@fixture()
def tx_rest_json() -> Json:
    # If desired these two values have to be added manually,
    # Bitcoin Core does not include them.
    TRANSACTION_REST_JSON['timestamp_date'] = 100000
    TRANSACTION_REST_JSON['height'] = 1000
    return TRANSACTION_REST_JSON


@fixture()
def block_rest_json() -> Json:
    return BLOCK_REST_JSON


@fixture()
def blockv3_rest_json() -> Json:
    return BLOCKV3_REST_JSON


@fixture()
def chain_info_json() -> Json:
    return CHAIN_INFO_REST_JSON


@fixture()
def tx_candidate(tx_rest_json: Json) -> Transaction:
    return Transaction(tx_rest_json)


@fixture()
def txv3(blockv3_rest_json: Json) -> TransactionV3:
    tx = blockv3_rest_json['tx'][1]
    tx['timestamp_date'] = 100000
    tx['height'] = 1000
    return TransactionV3(tx)


@fixture()
def block_candidate(block_rest_json: Json) -> Block:
    return Block(block_rest_json)


@fixture()
def blockv3_candidate(blockv3_rest_json: Json) -> BlockV3:
    return BlockV3(blockv3_rest_json)
