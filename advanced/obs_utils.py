from logging import disable, Formatter, getLogger, Logger, INFO, FileHandler
from sys import maxsize
from typing import Dict, Tuple, Any, Optional

from IPython.core.display import display_markdown
from psutil import virtual_memory
from psutil._common import bytes2human


def print_error(title: str, message: str) -> None:
    display_markdown(f'#### {title}:', raw=True)
    display_markdown(message, raw=True)


def get_logger(log_setting: str, name: str) -> Logger:
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
    Figure out and return appropriate start height and end height for the block scan.
    Use info from `getblockchaininfo` RPC call to manage pruning.
    Raise exceptions and print errors if they are invalid.
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
    if start < 0:
        # Start height is abs(start) blocks in the past.
        # Get current total number of blocks
        block_count: int = (info['blocks'])
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
    Check system memory, if `memory_limiy` is not provided, return % memory used.
    If a limit is provided, raise MemoryError if the limit is reached.
    """
    memory: Any = virtual_memory()
    if memory_limit and (memory.percent > memory_limit):
        raise MemoryError(f'Running out of memory (total: {bytes2human(memory.total)}, used: {memory.percent}%)')
    return int(memory.percent)
