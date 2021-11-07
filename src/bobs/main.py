from asyncio import run

from bobs.cli.commands import get_args
from bobs.cli.ui import print_result
from bobs.network.rest import RestClient
from bobs.obs.filters import TxFilter
from bobs.obs.scan import scan_blocks, scan_mem
from bobs.settings import Settings


async def main_async():
    args = get_args()
    settings = Settings.from_file(args.settings)

    try:
        filters = (TxFilter(settings['filters'][key], key) for key in args.filters)
    except KeyError:
        raise ValueError(f'Incorrect filter arguments: {args.filters}')
    async with RestClient(endpoint=settings['network']['endpoint']) as rest:
        if args.target == 'blocks':
            txs = await scan_blocks(args.start, args.end, rest, settings, *filters)
        elif args.target == 'mempool':
            txs = await scan_mem(rest, settings, *filters)
        print_result(txs, args.details, fmt=args.format)


def main():
    run(main_async())


if __name__ == '__main__':
    main()
