"""
Utilities for the observatory
"""

from logging import disable, Formatter, getLogger, Logger, INFO, FileHandler
from sys import maxsize
from typing import Tuple

from bobs.cli.ui import print_error
from bobs.types import Json
from psutil import virtual_memory  # type: ignore[import] # No type-hinting
from psutil._common import bytes2human  # type: ignore[import] # No type-hinting


def get_logger(log_setting: str, name: str) -> Logger:
    """
    Get a basic logger using value from settings file.
    """
    logger = getLogger(name)
    f_handler = FileHandler('log.txt')
    if not log_setting:
        disable(maxsize)
    elif log_setting.lower() == 'info':
        logger.setLevel(INFO)
        f_handler.setLevel(INFO)
    f_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)
    return logger


# pylint: disable-next=too-many-branches # TODO: for now is fine but it needs cleaning
def parse_start_and_end(start: int,
                        end: int,
                        info: Json,
                        force: bool) -> Tuple[int, int]:
    """
    Figure out and return appropriate start height and end height for blockchain scan.
    Use info from `chaininfo` Dict to manage pruning.
    Raise exceptions and print errors if they are invalid.

    **Examples:**

    >>> # Fake getblockchaininfo dict
    >>> fake_info = {'blocks': 100, 'pruneheight': 50, 'pruned': True}
    >>> s, e = parse_start_and_end(60, 80, fake_info, False)
    >>> print(s, e)
    60 80

    You can also give **negative** values to `start` and this will scan the last chosen blocks **depending** on the
    `end` value.
    This will search for transactions in the last 10 blocks.

    >>> s, e = parse_start_and_end(-10, 0, fake_info, False)
    >>> print(s, e)
    91 100

    This will search for transaction in 5 block starting from ten blocks ago.

    >>> s, e = parse_start_and_end(-10, 5, fake_info, False)
    >>> print(s, e)
    91 95

    By passing force=True you can force a start value even if you passed an invalid start argument due to pruning.
    The lowest available height will be used.
    If force=False ValueError is raised in this cases.

    >>> s, e = parse_start_and_end(30, 80, fake_info, True)
    >>> print(s, e)
    50 80
    """
    if not isinstance(start, int):
        print_error('Invalid `start`', 'Start height is not a valid integer number')  # type: ignore[unreachable]
        raise TypeError
    if not isinstance(end, int):
        print_error('Invalid `end`', 'End height is not a valid integer number')  # type: ignore[unreachable]
        raise TypeError
    if end < 0:
        print_error('Invalid `end`', 'End height cannot be negative')
        raise ValueError
    if start > end:
        print_error('Invalid `start`', f'Start height ({start}) is higher than end height ({end})')
        raise ValueError
    if 'pruned' not in info or 'blocks' not in info:
        print_error('Blockchain info data malformed', 'Blockchain info data malformed:\n\n {info}')
        raise ValueError
    if start > info['blocks']:
        print_error('Invalid `start`', f'Start height ({start}) is higher than max height ({info["blocks"]})')
        raise ValueError
    if end > info['blocks']:
        print_error('Invalid `end`', f'Start height ({end}) is higher than max height ({info["blocks"]})')
        raise ValueError
    if start < 0:
        # Start height is abs(start) blocks in the past.
        # Get current total number of blocks
        try:
            block_count: int = info['blocks']
        except KeyError as err:
            print_error('Blockchain info data malformed',
                        f'Blockchain info data does not contain the number of blocks:\n\n {info}')
            raise ValueError from err
        if end == 0:
            # Scan till most recent available block
            end = block_count
            start = end + start + 1
        else:
            # Scan for 'end' block or till most recent available block
            start = block_count + start + 1
            potential_end: int = start + end - 1
            end = potential_end if potential_end <= block_count else block_count
    if info['pruned'] is True:
        pruneheight: int = info['pruneheight']
        if end < pruneheight:
            print_error('Invalid `end`',
                        f'End block height is lower than the lowest-height complete block stored ({info["pruneheight"]})')
            raise ValueError
        if start < pruneheight:
            if force:
                # Start scanning from the lowest available block
                start = pruneheight
            else:
                error_msg = 'Start block height is lower than the lowest-height complete block stored ' \
                            f'({pruneheight}), if you want to scan anyway starting from lowest available height ' \
                            'add argument `force=True`'
                print_error('Invalid `start`', error_msg)
                raise ValueError
    return start, end


def check_memory(memory_limit: int = 0) -> int:
    """
    Check system memory, if `memory_limit` is not provided, return % memory used.
    If a limit is provided, additionally raise MemoryError if the limit is reached.
    """
    memory = virtual_memory()
    used = int(memory.percent)
    if 0 < memory_limit < used:
        raise MemoryError(f'Running out of memory (total: {bytes2human(memory.total)}, used: {used}%)')
    return used
