"""
Commands, arguments, and parsers
"""

from argparse import ArgumentParser, Namespace, ArgumentTypeError
from os.path import isdir


def dir_path(path: str) -> str:
    """
    Check given path actually corresponds to a directory
    """
    if isdir(path):
        return path
    raise ArgumentTypeError(f"{path} is not a valid path")


def get_args() -> Namespace:
    """
    Parse and return command line arguments.
    """
    parser = ArgumentParser(description='A Bitcoin observatory to monitor and scan given customizable filters')
    parser.add_argument('-f',
                        '--filter',
                        action='append',
                        type=str,
                        default=[],
                        help="The name of the filter to use (it has to be declared in settings.toml),"
                             " can be set multiple times")
    parser.add_argument('-d',
                        '--details',
                        action='count',
                        help="Increase result output details, can be set multiple times to amplify the effect")
    parser.add_argument('-t',
                        '--target',
                        type=str,
                        choices=['blocks', 'mempool'],
                        default='blocks',
                        help='What structure to look at, default is `blocks`')
    parser.add_argument('-c',
                        '--candidate',
                        type=str,
                        choices=['block', 'blockv3', 'tx', 'txv2', 'txv3'],
                        default='txv3',
                        help='The object to compare against the criteria')
    parser.add_argument('-fmt',
                        '--format',
                        type=str,
                        default='fancy_grid',
                        help="Format to pass to tabulate() for table formatting. (default 'fancy_grid')")
    parser.add_argument('-se',
                        '--settings',
                        type=dir_path,
                        help="Path to settings.toml file, default is current directory. If file not present, create it")
    parser.add_argument('-fa',
                        '--favorite',
                        type=str,
                        default='',
                        help="Use one of the favorite from settings, this overrides all other options."
                             "Currently not implemented")

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
