"""
Objects and iterators to fetch and process data from outside sources.
Currently mostly Bitcoin Core REST and ZMQ APIs.
"""

from abc import ABC, abstractmethod
from asyncio import Semaphore, create_task, gather, run, Lock
from multiprocessing import Process, Queue
from sys import byteorder
from typing import Optional, Iterator, ClassVar, Type, List

from bobs.network.rest import Rest, RestApi
from bobs.obs.candidates import Candidate, BlockV3, Block, MempoolTx, MempoolTxV2, MempoolTxV3, TransactionV3
from bobs.types import Json, RawData, Bytes, Any_
from orjson import loads, dumps


class Target(ABC):
    """
    Base Target object.

    A target is defined as a collection of Candidate objects.
    It is never instantiated directly but always through context manager.

    Encapsulate a Gatherer process, which writes the result of some IO to a Queue.

    The gatherer starts as soon as a Target instance is created, if the desired target includes a lot
    of candidates, the bytes response for all these objects will be stored in the Queue (so in memory)
    as they come until you get them through the `candidates` or `next` APIs.
    """

    # If gatherer process fails to join() in TIMEOUT seconds, kill it
    _TIMEOUT: ClassVar[int] = 3
    # The Candidate object for the result, subclasses should override it
    _CANDIDATE: ClassVar[Type[Candidate]] = Candidate

    __slots__ = ('endpoint', '_gatherer', '_result_queue')

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        # TODO: There is a deadlock between the 2 processes when using Pipe() instead of Queue(),
        # find a way to solve it because Pipe() would be the best solution.
        self._result_queue: Queue[bytes] = Queue()
        self._gatherer: Process = Process(target=self._gatherer_process,
                                          name='Gatherer')
        self._start()

    def __enter__(self) -> 'Target':
        return self

    def __exit__(self, exc_type: Any_, exc_val: Any_, exc_tb: Any_) -> None:
        self._stop()

    def _start(self) -> None:
        """
        Start the Gatherer process.
        """
        if self._gatherer.is_alive():
            raise RuntimeError('Cannot start an already running Gatherer')
        self._gatherer.start()
        if not self._gatherer.is_alive():
            raise RuntimeError("Gatherer process couldn't start")

    def _stop(self) -> None:
        """
        Stop gatherer process and close result Queue.
        """
        self._result_queue.close()
        self._gatherer.terminate()
        self._gatherer.join(self._TIMEOUT)
        if self._gatherer.is_alive():
            self._gatherer.kill()
            self._gatherer.join()

    def _gatherer_process(self) -> None:
        """
        This is the target of multiprocessing.Process().
        Run the worker in a separate process and put results in the result Queue.
        """
        run(self._worker())

    @abstractmethod
    async def _worker(self) -> None:
        """
        The main gatherer worker.
        """

    def _get_buffers(self) -> Iterator[Bytes]:
        """
        Compute and return a bytearray with the next complete buffer of bytes from the result Queue.
        This is the concatenation of all chunks until a b'' chunk is found.
        Subclasses should reimplement if needed to add custom logic.

        This blocks until something is put in the result Queue.
        """
        buffer = bytearray()
        while True:
            chunk = self._result_queue.get()
            if chunk == b'':
                yield buffer
                buffer = bytearray()
                continue
            if chunk == b'END':
                break
            buffer += chunk

    def _get_raw_candidates(self) -> Iterator[Json]:
        """
        Return a map iterator which processes the buffers and yields raw candidates in Dict form.
        Subclasses should reimplement if needed to add custom logic.
        """
        return map(loads, self._get_buffers())

    @property
    def candidates(self) -> Iterator[Candidate]:
        """
        Main Target API, return a map iterator which yields each Candidate
        object by consuming outputs from the result Queue.
        """
        return map(self._CANDIDATE, self._get_raw_candidates())

    @property
    def next(self) -> Optional[Candidate]:
        """
        Convenience method, return the next available Candidate or None if there are no more candidates available.
        """
        return next(self.candidates, None)


class Blocks(Target):
    """
    Base target to iterate block Candidates.
    """
    __slots__ = ('_start_height', '_end_height')

    _API: ClassVar[RestApi] = RestApi.BLOCK_NO_DETAILS
    _CANDIDATE: ClassVar[Type[Block]] = Block

    def __init__(self, endpoint: str, start: int, end: int) -> None:
        self._start_height = start
        self._end_height = end
        super().__init__(endpoint)

    async def _worker(self) -> None:
        async def task(height: int) -> None:
            async with sem:
                stream = await rest.get_chunks(self._API, await rest.get_blockhash(height))
                # Process one response at a time.
                # Bitcoin Core is synchronous anyway, but we still get a benefit from
                # doing all the dance till here concurrently.
                # The lock also helps not to mess up the Queue stream.
                async with lock:
                    async for chunk in stream:
                        self._result_queue.put_nowait(chunk)
                    self._result_queue.put_nowait(b'')

        sem = Semaphore(3)
        lock = Lock()
        async with Rest(endpoint=self.endpoint) as rest:
            tasks = (create_task(task(height)) for height in range(self._start_height, self._end_height + 1))
            await gather(*tasks)
        self._result_queue.put_nowait(b'END')


class BlocksV3(Blocks):
    __slots__ = ()

    _API: ClassVar[RestApi] = RestApi.BLOCK
    _CANDIDATE: ClassVar[Type[BlockV3]] = BlockV3


class BlockTxsV3(BlocksV3):
    """
    Target to iterate all the transactions in a block at verbosity 3.
    """

    __slots__ = ()

    _CANDIDATE: ClassVar[Type[TransactionV3]] = TransactionV3  # type: ignore[assignment] # We want to override the

    # parent type with a different type

    def _get_raw_candidates(self) -> Iterator[Json]:
        for buffer in self._get_buffers():
            block: Json = loads(buffer)
            tx: Json
            for tx in block['tx']:
                tx['timestamp_date'] = block['time']
                tx['height'] = block['height']
                yield tx


class MempoolTxs(Target):
    """
    Base target to iterate fee related transaction info only.
    """

    __slots__ = ()

    _CANDIDATE: ClassVar[Type[MempoolTx]] = MempoolTx

    async def _worker(self) -> None:
        async with Rest(endpoint=self.endpoint) as rest:
            async for chunk in await rest.get_chunks(RestApi.MEMPOOL_CONTENT):
                self._result_queue.put_nowait(chunk)
            self._result_queue.put_nowait(b'')

    def _get_raw_candidates(self) -> Iterator[Json]:
        try:
            for txid, tx in loads(next(self._get_buffers())).items():
                tx['txid'] = txid
                yield tx
        except StopIteration:
            return


class MempoolTxsV2(Target):
    """
    Base target to iterate mempool transactions.
    """

    __slots__ = ()

    _CANDIDATE: ClassVar[Type[MempoolTxV2]] = MempoolTxV2

    async def _worker(self) -> None:
        async def task(txid: str, data: RawData) -> None:
            async with sem:
                self._result_queue.put_nowait(await rest.get_bytes(RestApi.TX, txid))
                self._result_queue.put_nowait(data['height'].to_bytes(3, byteorder=byteorder))
                self._result_queue.put_nowait(data['time'].to_bytes(8, byteorder=byteorder))

        sem = Semaphore(3)
        async with Rest(endpoint=self.endpoint) as rest:
            tasks = (create_task(task(txid, data)) for txid, data in (await rest.get_mempool(True)).items())
            await gather(*tasks)
        self._result_queue.put_nowait(b'END')

    def _get_buffers(self) -> Iterator[bytes]:
        while True:
            buffer = self._result_queue.get()
            if buffer == b'END':
                break
            yield buffer

    def _get_raw_candidates(self) -> Iterator[Json]:
        buffers = self._get_buffers()
        for buffer in buffers:
            tx: Json = loads(buffer)
            try:
                height = int.from_bytes(next(buffers), byteorder=byteorder)
                time = int.from_bytes(next(buffers), byteorder=byteorder)
            except StopIteration:
                return
            tx['timestamp_date'] = time
            tx['height'] = height
            yield tx


class MempoolTxsV3(MempoolTxsV2):
    __slots__ = ()

    _CANDIDATE: ClassVar[Type[MempoolTxV3]] = MempoolTxV3

    async def _worker(self) -> None:

        async def update_inputs(tx_input: Json) -> None:
            utxos: List[Json] = (await rest.get_utxos(f"{tx_input['txid']}-{tx_input['vout']}"))[
                'utxos']
            if not utxos:
                # It's spending from another mempool transaction
                utxo: Json = (await rest.get_tx(tx_input['txid']))['vout'][tx_input['vout']]
                # No height
                utxo['height'] = 0
            else:
                utxo = utxos[0]
            tx_input['prevout'] = utxo

        async def task(txid: str, data: RawData) -> None:
            """
            Given a TXID, gets the incomplete mempool transaction, asynchronously calls get_utxos/get_tx to
            get prevout information for each transaction input.
            """
            async with sem:
                tx: Json = await rest.get_tx(txid)
                tx['height'] = data['height']
                tx['timestamp_date'] = data['time']
                await gather(*map(update_inputs, tx['vin']))
                self._result_queue.put_nowait(dumps(tx))

        sem = Semaphore(3)
        async with Rest(endpoint=self.endpoint) as rest:
            tasks = (create_task(task(txid, data)) for txid, data in (await rest.get_mempool(True)).items())
            await gather(*tasks)
        self._result_queue.put_nowait(b'END')

    def _get_raw_candidates(self) -> Iterator[Json]:
        for buffer in self._get_buffers():
            yield loads(buffer)
