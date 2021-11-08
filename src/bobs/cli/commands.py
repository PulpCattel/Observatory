"""
Commands, arguments, and parsers
"""

from argparse import ArgumentParser, Namespace, ArgumentTypeError
from os.path import isdir


def dir_path(path):
    """
    Check given path actually corresponds to a directory
    """
    if isdir(path):
        return path
    raise ArgumentTypeError(f"{path} is not a valid path")


def get_args() -> Namespace:
    """
    ArgumentParser for Bobs
    """
    parser = ArgumentParser(description='A Bitcoin observatory to monitor and scan given customizable filters')
    parser.add_argument('-f',
                        '--filters',
                        action='append',
                        type=str,
                        default=[],
                        help="The name of the filters to use (they have to be declared in settings.toml).")
    parser.add_argument('-d',
                        '--details',
                        action='count',
                        help="Increase table details")
    parser.add_argument('-t',
                        '--target',
                        type=str,
                        choices=['blocks', 'mempool'],
                        default='blocks',
                        help='What to scan, default is `blocks`')
    parser.add_argument('-fmt',
                        '--format',
                        type=str,
                        default='fancy_grid',
                        help="Format to pass to tabulate() for table formatting. (default 'fancy_grid')")
    parser.add_argument('-se',
                        '--settings',
                        type=dir_path,
                        help="Path to settings.toml file, default is current directory. If file not present, create it.")

    subparsers = parser.add_subparsers()
    parser_scan = subparsers.add_parser('scan',
                                        description='Scan past data using given filters',
                                        help='Scan past data using given filters')
    parser_scan.add_argument('-s',
                             '--start',
                             type=int,
                             help='Start block height')
    parser_scan.add_argument('-e',
                             '--end',
                             type=int,
                             default=0,
                             help='End block height')
    # TODO: implement monitor
    parser_scan = subparsers.add_parser('monitor',
                                        description='Monitor new coming data using given filters',
                                        help='Monitor new coming data using given filter, currently not implemented')
    return parser.parse_args()
