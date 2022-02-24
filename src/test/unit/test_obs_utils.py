""""
Tests for the utils module
"""

from typing import Dict, Union

from bobs.obs.utils import parse_start_and_end, check_memory
from pytest import raises

# Fake getblockchaininfo dict
info: Dict[str, Union[int, bool]] = {'blocks': 100,
                                     'pruneheight': 50,
                                     'pruned': True}


def test_parse_start_and_end() -> None:
    with raises(ValueError):
        parse_start_and_end(-110, 0, info, False)
    with raises(ValueError):
        parse_start_and_end(30, 40, info, False)
    with raises(ValueError):
        parse_start_and_end(90, 80, info, False)
    with raises(TypeError):
        parse_start_and_end('wrong', 100, info, False)
    with raises(TypeError):
        parse_start_and_end(70, 'wrong', info, False)
    with raises(ValueError):
        parse_start_and_end(70, -10, info, False)


def test_check_memory() -> None:
    memory_used = check_memory()
    assert isinstance(memory_used, int)
    with raises(MemoryError):
        check_memory(memory_used // 2)
    memory_used = check_memory()
    # This should not raise any exception
    check_memory(memory_used * 2)
