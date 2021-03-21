from logging import disable, Formatter, getLogger, Logger, INFO, FileHandler
from sys import maxsize
from typing import Union, Dict, Tuple, Any

from IPython.core.display import display_markdown


def print_error(title: str, message: str) -> None:
    display_markdown(f'#### {title}:', raw=True)
    display_markdown(message, raw=True)


def get_logger(log_setting: Union[str, bool], name: str) -> Logger:
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
                        force: bool) -> Union[Tuple[int, int], Tuple[None, None]]:
    """
    Figures out and returns appropriate start height and end height for the scan.
    Uses info from `getblockchaininfo` RPC call to manage pruning.
    Return double None and prints errors if they are invalid.
    """
    if not isinstance(start, int):
        print_error('Invalid `start`', 'Start height is not a valid integer number')
        return None, None
    if not isinstance(end, int):
        print_error('Invalid `end`', 'End height is not a valid integer number')
        return None, None
    if end < 0:
        print_error('Invalid `end`', 'End height cannot be negative')
        return None, None
    if start > end:
        error_msg = f'Start height ({start}) is higher than end height ({end})'
        print_error('Invalid `start`', error_msg)
        return None, None
    if start < 0:
        # Start height is abs(start) blocks in the past.
        # Get current total number of blocks
        block_count: int = (info['blocks'])
        if not end:
            # Scan till most recent available block
            end: int = block_count
            start: int = end + start + 1
        else:
            # Scan for 'end' block or till most recent available block
            start: int = block_count + start + 1
            potential_end: int = start + end - 1
            end: int = potential_end if potential_end <= block_count else block_count
    if info['pruned'] is True:
        if end < info['pruneheight']:
            print_error('Invalid `end`',
                        f'End block height is lower than the lowest-height complete block stored ({info["pruneheight"]})')
            return None, None
        if start < info['pruneheight']:
            if force:
                # Start scanning from the lowest available block
                start: int = info['pruneheight']
            else:
                error_msg = 'Start block height is lower than the lowest-height complete block stored ' \
                            f'({info["pruneheight"]}), if you want to scan anyway starting from lowest available height ' \
                            'add argument `force=True`'
                print_error('Invalid `start`', error_msg)
                return None, None
    return start, end
