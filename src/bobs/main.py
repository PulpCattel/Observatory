"""
Bobs main logic
"""

from bobs.cli.commands import get_args
from bobs.cli.ui import print_result, print_greetings
from bobs.obs.scan import scan_blocks, scan_mem
from bobs.settings import Settings


def main() -> None:
    args = get_args()
    settings = Settings.from_file(args.settings)
    print_greetings(args.filter)
    try:
        filters = [settings['filters'][key] for key in args.filter]
    except KeyError as err:
        raise ValueError(f'Incorrect filter arguments: {args.filter}') from err
    if args.target == 'blocks':
        txs = scan_blocks(args.start, args.end, settings, args.candidate, *filters)
    elif args.target == 'mempool':
        txs = scan_mem(settings, args.candidate, *filters)
    # TODO
    else:
        raise NotImplementedError
    print_result(list(txs), args.details, fmt=args.format)  # type: ignore[arg-type] # UI related, TODO: fix


if __name__ == '__main__':
    main()
