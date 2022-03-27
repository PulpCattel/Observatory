"""
Test basic inner methods of Target abstract class.
"""
# pylint: disable=protected-access
from queue import Empty

import pytest
from bobs.obs.candidates import Candidate
from bobs.obs.targets import Target
from orjson import dumps


class FakeTarget(Target):
    """
    Dumb target.
    """

    async def _worker(self) -> None:
        pass

    def _start(self) -> None:
        """
        Do not start a process.
        """


def test_get_buffers() -> None:
    target = FakeTarget('')
    target._result_queue.put_nowait(b'foo')
    # get_buffers() by default return a chunk of bytes only when b'' is found.
    with pytest.raises(Empty):
        # There is an item in the Queue, but it won't return it yet
        # and therefore the Queue will throw when it tries to get a 2nd item
        # looking for b''
        # Without a timeout it would block forever, it's nice to test this by increasing the timeout.
        next(target._get_buffers(timeout=0.001))
    target._result_queue.put_nowait(b'foo')
    target._result_queue.put_nowait(b'')
    # Now it should return an item
    assert next(target._get_buffers()) == b'foo'
    # When b'END' is found, the stream should stop
    target._result_queue.put_nowait(b'foo')
    target._result_queue.put_nowait(b'END')
    with pytest.raises(StopIteration):
        # There was an item in the Queue, but no b'', so no item should be returned.
        next(target._get_buffers())
    # With the extra b'' all should work normally
    target._result_queue.put_nowait(b'foo')
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'END')
    assert next(target._get_buffers()) == b'foo'
    with pytest.raises(StopIteration):
        next(target._get_buffers())
    # The buffer should include all chunks until b''
    target._result_queue.put_nowait(b'foo')
    target._result_queue.put_nowait(b'bar')
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'END')
    assert next(target._get_buffers()) == b'foobar'
    with pytest.raises(StopIteration):
        next(target._get_buffers())
    # Test support for multiple buffers
    target._result_queue.put_nowait(b'foobar')
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'foo')
    target._result_queue.put_nowait(b'bar')
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'END')
    assert next(target._get_buffers()) == b'foobar'
    assert next(target._get_buffers()) == b'foobar'
    with pytest.raises(StopIteration):
        next(target._get_buffers())
    # Test the iterator can be cached and it keeps working as new item are added
    target._result_queue.put_nowait(b'barfoo')
    target._result_queue.put_nowait(b'')
    buffers = target._get_buffers()
    assert next(buffers) == b'barfoo'
    target._result_queue.put_nowait(b'foo')
    target._result_queue.put_nowait(b'bar')
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'foobar')
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'END')
    assert next(buffers) == b'foobar'
    assert next(buffers) == b'foobar'
    with pytest.raises(StopIteration):
        next(target._get_buffers())


def test_get_raw_candidates() -> None:
    target = FakeTarget('')
    test_dict = {'foo': 'bar'}
    target._result_queue.put_nowait(dumps(test_dict))
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'END')
    assert next(target._get_raw_candidates()) == test_dict
    with pytest.raises(StopIteration):
        next(target._get_raw_candidates())


def test_candidates() -> None:
    target = FakeTarget('')
    test_dict = {'foo': 'bar'}
    target._result_queue.put_nowait(dumps(test_dict))
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'END')
    candidate = next(target.candidates)
    assert isinstance(candidate, Candidate)
    assert candidate.raw_data == test_dict
    with pytest.raises(StopIteration):
        next(target.candidates)


def test_next() -> None:
    target = FakeTarget('')
    test_dict = {'foo': 'bar'}
    target._result_queue.put_nowait(dumps(test_dict))
    target._result_queue.put_nowait(b'')
    target._result_queue.put_nowait(b'END')
    candidate = target.next
    assert isinstance(candidate, Candidate)
    assert candidate.raw_data == test_dict
    assert target.next is None
