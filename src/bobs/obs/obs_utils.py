"""
Utilities for the observatory
"""

from logging import disable, Formatter, getLogger, Logger, INFO, FileHandler
from sys import maxsize
from typing import Dict, Tuple, Any, Optional

from psutil import virtual_memory
from psutil._common import bytes2human


def print_error(title: str, message: str) -> None:
    """
    Pretty print errors
    """
    print(f'#### {title}:')
    print(message)


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


def parse_start_and_end(start: int,
                        end: int,
                        info: Dict[str, Any],
                        force: bool) -> Tuple[int, int]:
    """
    Figure out and return appropriate start height and end height for blockchain scan.
    Use info from `chaininfo` REST call to manage pruning.
    Raise exceptions and print errors if they are invalid.

    **Examples**

    start = 100
    end = 200
    Will search for transactions between block 100 and block 200 included.

    You can also give **negative** values to `start` and this will scan the last chosen blocks **depending** on the
    `end` value.
    start = -10
    end = 0
    Will search for transactions in the last 10 blocks.

    start = -10
    end = 5
    Will search for transanction in 5 block starting from ten blocks ago.

    """
    if not isinstance(start, int):
        print_error('Invalid `start`', 'Start height is not a valid integer number')
        raise TypeError
    if not isinstance(end, int):
        print_error('Invalid `end`', 'End height is not a valid integer number')
        raise TypeError
    if end < 0:
        print_error('Invalid `end`', 'End height cannot be negative')
        raise ValueError
    if start > end:
        print_error('Invalid `start`', f'Start height ({start}) is higher than end height ({end})')
        raise ValueError
    if 'pruned' not in info:
        print_error('Blockchain info data malformed',
                    f'Blockchain info data does not contain the prune status:\n\n {info}')
        raise ValueError
    if start < 0:
        # Start height is abs(start) blocks in the past.
        # Get current total number of blocks
        try:
            block_count: int = (info['blocks'])
        except KeyError:
            print_error('Blockchain info data malformed',
                        f'Blockchain info data does not contain the number of blocks:\n\n {info}')
            raise ValueError
        if not end:
            # Scan till most recent available block
            end = block_count
            start = end + start + 1
        else:
            # Scan for 'end' block or till most recent available block
            start = block_count + start + 1
            potential_end: int = start + end - 1
            end = potential_end if potential_end <= block_count else block_count
    if info['pruned'] is True:
        if end < info['pruneheight']:
            print_error('Invalid `end`',
                        f'End block height is lower than the lowest-height complete block stored ({info["pruneheight"]})')
            raise ValueError
        if start < info['pruneheight']:
            if force:
                # Start scanning from the lowest available block
                start = info['pruneheight']
            else:
                error_msg = 'Start block height is lower than the lowest-height complete block stored ' \
                            f'({info["pruneheight"]}), if you want to scan anyway starting from lowest available height ' \
                            'add argument `force=True`'
                print_error('Invalid `start`', error_msg)
                raise ValueError
    return start, end


def check_memory(memory_limit: Optional[int] = None) -> Optional[int]:
    """
    Check system memory, if `memory_limit` is not provided, return % memory used.
    If a limit is provided, raise MemoryError if the limit is reached.
    """
    memory = virtual_memory()
    if memory_limit and (memory.percent > memory_limit):
        raise MemoryError(f'Running out of memory (total: {bytes2human(memory.total)}, used: {memory.percent}%)')
    return int(memory.percent)
