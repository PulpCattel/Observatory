"""
Pytest helper classes and fixtures
"""

from asyncio import get_event_loop, AbstractEventLoop
from typing import Generator, AsyncGenerator, Dict, Any

from bobs.network.rest import RestClient
from bobs.settings import Settings
from pytest import fixture, mark


@fixture(scope='session')
def settings_() -> Generator[Dict[str, Any], None, None]:
    """
    Yield Settings dictionary, shared across the entire test session
    """
    yield Settings.from_file(force_exist=True)


@fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    """
    Yield asyncio event loop shared across the entire session
    """
    loop = get_event_loop()
    yield loop
    loop.close()


@fixture(scope='session')
@mark.asyncio
async def uninit_rest() -> AsyncGenerator[RestClient, None]:
    """
    Yield REST client shared across the entire test session
    """
    async with RestClient() as rest:
        yield rest


@fixture(scope='session')
@mark.asyncio
async def init_rest(settings_) -> AsyncGenerator[RestClient, None]:
    """
    Yield REST client initialized from settings configuration file, shared across the entire test session
    """
    async with RestClient(endpoint=settings_['network']['endpoint']) as rest:
        yield rest
