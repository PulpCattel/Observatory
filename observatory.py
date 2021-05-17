from asyncio import Semaphore, create_task, as_completed, all_tasks, run, CancelledError
from argparse import ArgumentParser
from collections import Counter
from time import time
from typing import List

from aiohttp import ClientConnectionError, ClientResponseError
from matplotlib.pyplot import plot_date, plot, legend, savefig, style, subplots
import numpy as np
from IPython.display import display_markdown, display
from pandas import DataFrame, read_feather, option_context, get_option
from psutil import virtual_memory
from psutil._common import bytes2human
from tqdm import tqdm

from advanced.obs_utils import get_logger, print_error, parse_start_and_end
from advanced.containers import Tx
from advanced.rpc_client import RpcClient
from settings import settings

style.use('fivethirtyeight')


# MAIN
async def create_dataframe(start, end, *filters, force=False):
    start_time = time()
    semaphore = Semaphore(settings['scan_limit'])
    logger = get_logger(settings['logging'], __name__)

    txids = []
    versions = []
    sizes = []
    vsizes = []
    weights = []
    locktimes = []
    inputs = []
    n_ins = []
    outputs = []
    n_outs = []
    n_eqs = []
    dens = []
    abs_fees = []
    rel_fees = []
    heights = []
    dates = []

    async def scan(blockheight):

        blockhash = await rpc_client.getblockhash(blockheight)
        block = await rpc_client.getblock(blockhash, 3)
        while block['tx']:
            tx = Tx(block['tx'].pop(0), block['time'], blockheight)
            for f in filters:
                if f.match(tx):
                    txids.append(tx.txid)
                    versions.append(tx.version)
                    sizes.append(tx.size)
                    vsizes.append(tx.vsize)
                    weights.append(tx.weight)
                    locktimes.append(tx.locktime)
                    inputs.append([inp for inp in tx.inputs])
                    n_ins.append(tx.n_in)
                    outputs.append([out for out in tx.outputs])
                    n_outs.append(tx.n_out)
                    n_eqs.append(tx.n_eq)
                    dens.append(tx.den)
                    abs_fees.append(tx.abs_fee)
                    rel_fees.append(tx.rel_fee)
                    heights.append(tx.height)
                    dates.append(tx.date)
                    break
        return

    async def sem_scan(blockheight):
        async with semaphore:
            mem = virtual_memory()
            if mem.percent > settings['memory_limit']:
                raise MemoryError(f'Running out of memory (total: {bytes2human(mem.total)}, used {mem.percent}%)')
            return await scan(blockheight)

    rpc_client = await RpcClient.get_client(
        user=settings['rpc_user'],
        pwd=settings['rpc_password'],
        endpoint=settings['rpc_endpoint'],
    )
    rpc_client.add_methods('getblockhash', 'getblock', 'getblockstats', 'getblockchaininfo')
    try:
        info = await rpc_client.getblockchaininfo()
    except ClientConnectionError:
        logger.error('Connection error', exc_info=True)
        print_error('Connection error', 'Cannot establish connection with Bitcoin Knots')
        await rpc_client.close()
        return
    except ClientResponseError:
        logger.error('Response error', exc_info=True)
        print_error('Response error', 'Invalid RPC credentials')
        await rpc_client.close()
        return
    start, end = parse_start_and_end(start, end, info, force)
    if not start:
        return
    start_msg = f'Start scanning from block **{start}** to block **{end}** included...'
    logger.info(start_msg)
    display_markdown(start_msg, raw=True)
    tasks = (create_task(sem_scan(blockheight)) for blockheight in range(start, end + 1))
    try:
        for coro in tqdm(as_completed(list(tasks))):
            await coro
    except CancelledError:
        logger.warning('Tasks canceled', exc_info=True)
        return
    except MemoryError as e:
        logger.warning('MemoryError', exc_info=True)
        print_error('Memory error', str(e))
        return
    except Exception as e:
        logger.error('Something went wrong', exc_info=True)
        print_error('Something went wrong', str(e))
        return
    finally:
        for task in all_tasks():
            task.cancel()
            try:
                await task
            except:
                pass
        await rpc_client.close()
    df = DataFrame({'txid': txids,
                    'version': np.array(versions, dtype='uint8'),
                    'size': np.array(sizes, dtype='uint32'),
                    'vsize': np.array(vsizes, dtype='uint32'),
                    'weight': np.array(weights, dtype='uint32'),
                    'locktime': np.array(locktimes, dtype='uint32'),
                    'inputs': [[inp.dict for inp in lst] for lst in inputs],
                    'n_in': np.array(n_ins, dtype='uint16'),
                    'outputs': [[out.dict for out in lst] for lst in outputs],
                    'n_out': np.array(n_outs, dtype='uint16'),
                    'n_eq': np.array(n_eqs, dtype='uint16'),
                    'den': np.array(dens, dtype='uint64'),
                    'abs_fee': np.array(abs_fees, dtype='uint32'),
                    'rel_fee': np.array(rel_fees, dtype='uint16'),
                    'height': np.array(heights, dtype='uint32'),
                    'date': np.array(dates, dtype='datetime64')})

    result_msg = f'Created dataframe of **{len(df)}** transactions in {round(time() - start_time, 2)}s'
    logger.info(result_msg)
    display_markdown(result_msg, raw=True)
    display_markdown('[Save dataframe](#Save-dataframe)', raw=True)
    display_markdown('[Start analysis](#Glimpse)', raw=True)
    return df.set_index('txid').sort_values('date') if len(df) else df


def save(filepath, df):
    start_time = time()
    if df.empty:
        print_error('Empty dataframe', 'Cannot save empty dataframe')
        return
    if not filepath:
        print_error('Empty filepath', 'Empty filepath is invalid')
        return
    try:
        df.reset_index().to_feather(f'{filepath}.ftr')
    except PermissionError:
        print_error('Permission error', f'Permission denied for `{filepath}`')
        return
    except FileNotFoundError:
        print_error('Filepath not found', f'Given filepath `{filepath}` not found')
        return
    except Exception as e:
        print_error('Something went wrong', str(e))
        return
    print(f'Dataframe succesfully saved in {round(time() - start_time, 2)}s')
    return


def load(filepath):
    start_time = time()
    if not filepath:
        print_error('Empty filepath', 'Empty filepath is invalid')
        return
    try:
        df = read_feather(f'{filepath}.ftr')
    except PermissionError:
        print_error('Permission error', f'Permission denied for `{filepath}`')
        return
    except FileNotFoundError:
        print_error('Filepath not found', f'Given filepath `{filepath}.ftr` not found')
        return
    except Exception as e:
        print_error('Something went wrong', str(e))
        return
    print(f'Dataframe succesfully loaded in {round(time() - start_time, 2)}s')
    display_markdown('[Start analysis](#Glimpse)', raw=True)
    return df.set_index('txid').sort_values('date')


def show_intro(df, n, sort_by):
    if df.empty:
        print_error('Empty dataframe', 'Cannot operate on empty dataframe')
        return
    if not isinstance(n, int):
        print_error('Invalid n_txs', f'Given n_txs `{n}` is not an integer number')
        return
    if sort_by and sort_by not in df.columns:
        print_error('Invalid sort_by', f'Given sort_by `{sort_by}` does not appear as column')
        return
    display_markdown(f'**{len(df)} total transactions**', raw=True)
    df = df[[column for column in df.columns if column not in ['inputs', 'outputs']]]
    if sort_by:
        df = df.sort_values(sort_by)
    with option_context('display.max_rows',
                        n if n > get_option('display.max_rows') else get_option('display.max_rows')):
        if n < 0:
            display(df.tail(abs(n)))
        else:
            display(df.head(n))


def show_stats(df):
    if df.empty:
        print_error('Empty dataframe', 'Cannot operate on empty dataframe')
        return
    return df[[column for column in df.columns if column not in ['inputs', 'outputs']]].describe()


def show_tx(df, txid, display_all=False):
    if df.empty:
        print_error('Empty dataframe', 'Cannot extrapolate tx from empty dataframe')
        return
    if not txid:
        print_error('Empty txid', 'Nothing to search, please provide a `txid`')
        return
    txs = df[df.index.str.contains(txid)]
    if txs.empty:
        print_error('Txid not found', f'Transaction **{txid}** is not in the dataframe')
        return
    with option_context('display.max_rows', None if display_all else get_option('display.max_rows'),
                        'display.max_colwidth', None):
        display(txs[[column for column in df.columns if column not in ['inputs', 'outputs']]])
        display_markdown('### Inputs', raw=True)
        input_df = DataFrame(tx_input for tx_inputs in txs.inputs for tx_input in tx_inputs)
        display(input_df.assign(available=input_df['txid'].isin(df.index)))
        display_markdown('### Outputs', raw=True)
        display(DataFrame(tx_output for tx_outputs in txs.outputs for tx_output in tx_outputs).set_index('vout'))
    return


def get_subplot():
    fig, ax = subplots()
    fig.set_size_inches(20, 10)
    ax.set_xlabel('Txs')
    return fig, ax


def save_graph(filepath):
    try:
        savefig(f'{filepath}.png', dpi=400, bbox_inches='tight')
    except PermissionError:
        print_error('Permission error', f'Permission denied for `{filepath}`')
        return
    except FileNotFoundError:
        print_error('Filepath not found', f'Given filepath `{filepath}` not found')
        return
    except Exception as e:
        print_error('Something went wrong', str(e))
        return
    return


def show_graph(df, column, filepath=''):
    if df.empty:
        print_error('Empty dataframe', 'Cannot plot empty dataframe')
    if not column:
        print_error('Empty column', 'Cannot plot empty column')
        return
    label_title = column.replace('_', ' ') if '_' in column else column
    fig, ax = get_subplot()
    ax.set_ylabel(label_title.title())
    ax.set_title(label_title.title())
    df = df.reset_index()
    ax.scatter(df.index, df[column], color='green')
    if filepath:
        save_graph(filepath)
    return


def show_volume(df, filepath=''):
    if df.empty:
        print_error('Empty dataframe', 'Cannot plot empty dataframe')
    inputs_vol: float = 0.0
    inputs_sums: List[float] = []
    eq_vol: float = 0
    eq_sums: List[float] = []
    for tx_inputs, tx_outputs in zip(df['inputs'], df['outputs']):
        for tx_input in tx_inputs:
            inputs_vol += tx_input['value'] / 1e8
        inputs_sums.append(inputs_vol)

        output_values = (tx_output["value"] for tx_output in tx_outputs)
        sizes_count = Counter(output_values)
        for size, count in sizes_count.items():
            if count > 1:
                eq_vol += (size / 1e8 * count)
        eq_sums.append(eq_vol)
    display_markdown(f'**Input** volume: {round(inputs_vol, 8)}', raw=True)
    display_markdown(f'**Equal output** volume: {round(eq_vol, 8)}', raw=True)
    fig, ax = get_subplot()
    ax.set_ylabel('BTC')
    ax.set_title('Volume')
    plot(inputs_sums, label='Input', color='blue')
    plot(eq_sums, label='Mixed', color='green')
    legend()
    if filepath:
        save_graph(filepath)
    return


def show_daily(df, filepath=''):
    if df.empty:
        print_error('Empty dataframe', 'Cannot plot empty dataframe')
    count_dates = Counter(df['date'].dt.normalize())
    counts = []
    daily_avg = []
    for count in count_dates.values():
        counts.append(count)
        avg = sum(counts) / len(counts)
        daily_avg.append(avg)
    display_markdown(f'**Average daily**: {round(daily_avg[-1], 1)}', raw=True)
    fig, ax = get_subplot()
    ax.set_ylabel('Num txs')
    ax.set_xlabel('Days')
    ax.set_title('Daily txs')
    x_values = [str(date).split()[0][-5:] for date in count_dates.keys()]
    plot_date(x_values, counts, label='Txs per day', color='blue', fmt='-')
    plot_date(x_values, daily_avg, label='Average', color='green', fmt='-')
    legend()
    fig.autofmt_xdate()
    if filepath:
        save_graph(filepath)
    return


if __name__ == '__main__':
    from ast import literal_eval
    from advanced.filters import TxFilter

    parser = ArgumentParser(description='Scan from start block height to end block height using given filter. '
                                                 'If you give it a filepath, the result dataframe will be saved.')
    parser.add_argument('start',
                        type=int,
                        help='Start block height')
    parser.add_argument('-e',
                        '--end',
                        type=int,
                        help='End block height')
    parser.add_argument('-f',
                        '--filter',
                        type=literal_eval,
                        help="Filter criteria.  Syntax {'criteria1':value1, 'criteria2':value2, ...}")
    parser.add_argument('-fp',
                        '--filepath',
                        help='Filepath where to save the result dataframe.')
    args = parser.parse_args()
    tx_filter = TxFilter(**args.filter) if args.filter else TxFilter()
    res = run(create_dataframe(args.start, args.end, tx_filter))
    if args.filepath:
        save(args.filepath, res)
