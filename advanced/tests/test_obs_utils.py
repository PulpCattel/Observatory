from inspect import currentframe, getfile
import os
import sys
from typing import Dict, Union
from pytest import raises

# Used to import from parent directory
current_dir: str = os.path.dirname(os.path.abspath(getfile(currentframe())))
parent_dir: str = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from obs_utils import parse_start_and_end

# Fake getblockchaininfo dict
info: Dict[str, Union[int, bool]] = {'blocks': 100,
        'pruneheight': 50,
        'pruned': True}


def test_parse_start_and_end(capsys) -> None:
    start, end = parse_start_and_end(-10, 0, info, False)
    assert start == 91
    assert end == 100
    start, end = parse_start_and_end(-10, 5, info, False)
    assert start == 91
    assert end == 95
    start, end = parse_start_and_end(70, 100, info, False)
    assert start == 70
    assert end == 100
    start, end = parse_start_and_end(30, 80, info, True)
    assert start == 50
    assert end == 80
    with raises(ValueError):
        parse_start_and_end(-110, 0, info, False)
        captured = capsys.readouterr()
        assert captured.out == "{'text/markdown': '#### Invalid `start`:'}\n{'text/markdown': 'Start block height is lower than the lowest-height complete block stored (50), if you want to scan anyway starting from lowest available height add argument `force=True`'}\n"
    with raises(ValueError):
        parse_start_and_end(30, 40, info, False)
        captured = capsys.readouterr()
        assert captured.out == "{'text/markdown': '#### Invalid `end`:'}\n{'text/markdown': 'End block height is lower than the lowest-height complete block stored (50)'}\n"
    with raises(ValueError):
        parse_start_and_end(90, 80, info, False)
        captured = capsys.readouterr()
        assert captured.out == "{'text/markdown': '#### Invalid `start`:'}\n{'text/markdown': 'Start height (90) is higher than end height (80)'}\n"
    with raises(TypeError):
        parse_start_and_end('wrong', 100, info, False)
        captured = capsys.readouterr()
        assert captured.out == "{'text/markdown': '#### Invalid `start`:'}\n{'text/markdown': 'Start height is not a valid integer number'}\n"
    with raises(TypeError):
        parse_start_and_end(70, 'wrong', info, False)
        captured = capsys.readouterr()
        assert captured.out == "{'text/markdown': '#### Invalid `end`:'}\n{'text/markdown': 'End height is not a valid integer number'}\n"
    with raises(ValueError):
        parse_start_and_end(70, -10, info, False)
        captured = capsys.readouterr()
        assert captured.out == "{'text/markdown': '#### Invalid `end`:'}\n{'text/markdown': 'End height cannot be negative'}\n"
