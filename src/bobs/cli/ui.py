"""
Functions and utilities to manage the command line interface
"""

from sys import argv
from typing import Iterable, Sequence

from bobs.obs.candidates import TransactionV3, Transaction
from bobs.types import Filter
from tabulate import tabulate

HEADERS_TXID_TABLE = ('txid',)
HEADERS_BASE_TABLE = ('txid', 'height', 'date')
HEADERS_DETAILED_TABLE = ('txid', 'version', 'size', 'vsize', 'weight', 'locktime',
                          'abs fee', 'rel fee', 'height', 'date')
HEADERS_INPUTS_TABLE = ('txid', 'height', 'value', 'vout', 'address', 'type', 'sequence')
HEADERS_OUTPUTS_TABLE = ('value', 'vout', 'address', 'type')
HEADERS_FULL_DETAIL_TABLE = ('txid', 'version', 'size', 'vsize', 'weight', 'locktime',
                             'abs fee', 'rel fee', 'height', 'date')


def print_error(title: str, message: str) -> None:
    """
    Pretty print errors.
    TODO: add colors
    """
    print(f'#### {title}:')
    print(message)


def print_greetings(filters: Iterable[Filter]) -> None:
    print('\nChosen filters:')
    for f in filters:
        print(f'\t{f}\n')
    print(f'Full command used: {" ".join(argv)}\n')


def print_result(txs: Sequence[TransactionV3],
                 details: int,
                 stats: bool = False,  # TODO
                 fmt: str = 'fancy_grid') -> None:
    """
    Print result table from an iterable of Tx candidates.
    Details represents the amount of information displayed (0, 1, 2, 3).
    If `stats`, an extra table with statistics about the sample will be printed
    right at the top.
    """
    print(f'\nFound {len(txs)} transaction:')
    print("\n")
    if details is None:
        print(txid_list(txs))
    elif details == 1:
        print(base_table(txs, fmt))
    elif details == 2:
        print(detailed_table(txs, fmt))
    elif details >= 3:
        full_detail_table(txs, fmt)
    print("\n")


def txid_list(txs: Iterable) -> str:
    """
    Return a list of TXIDs.
    """
    return '\n'.join(tx.txid for tx in txs)


def base_table(txs: Iterable, fmt: str) -> str:
    """
    Return a table with basic information about each transaction.
    """
    return tabulate(((tx.txid, tx.height, tx.date) for tx in txs),
                    headers=HEADERS_BASE_TABLE,
                    tablefmt=fmt)


def detailed_table(txs: Iterable, fmt: str) -> str:
    """
    Return a table with most of the details of each transaction.
    """
    return tabulate(((tx.txid, tx.version, tx.size, tx.vsize, tx.weight,
                      tx.locktime, tx.abs_fee, tx.rel_fee, tx.height, tx.date) for tx in txs),
                    headers=HEADERS_DETAILED_TABLE,
                    tablefmt=fmt)


def inputs_table(tx: TransactionV3, fmt: str) -> str:
    """
    Return table with all transaction inputs information.
    """
    if tx.is_coinbase:
        return tabulate(((None, None, None, None, None, None, tx_input['sequence']) for tx_input in tx.inputs),
                        headers=HEADERS_INPUTS_TABLE,
                        tablefmt=fmt)
    return tabulate(((tx_input['txid'], tx_input['prevout']['height'], tx_input['prevout']['value'],
                      tx_input['vout'], tx_input['prevout']['scriptPubKey']['address'],
                      tx_input['prevout']['scriptPubKey']['type'], tx_input['sequence']) for tx_input in tx.inputs),
                    headers=HEADERS_INPUTS_TABLE,
                    tablefmt=fmt)


def outputs_table(tx: Transaction, fmt: str) -> str:
    """
    Return table with all transaction inputs information.
    """
    return tabulate(((tx_output['value'], tx_output['n'], tx_output['scriptPubKey'].get('address', ''),
                      tx_output['scriptPubKey']['type']) for tx_output in tx.outputs),
                    headers=HEADERS_OUTPUTS_TABLE,
                    tablefmt=fmt)


def full_detail_table(txs: Iterable[TransactionV3], fmt: str) -> None:
    """
    Print multiple tables with all the details of each transaction plus inputs and outputs information.
    """
    for tx in txs:
        print('\n\n\n\n## Transaction\n')
        print(tabulate(((tx.txid, tx.version, tx.size, tx.vsize, tx.weight,
                         tx.locktime, tx.abs_fee, tx.rel_fee, tx.height, tx.date),),
                       headers=HEADERS_FULL_DETAIL_TABLE,
                       tablefmt=fmt))
        print(f'\n### {tx.n_in} inputs\n')
        print(inputs_table(tx, fmt))
        print(f'\n### {tx.n_out} outputs\n')
        print(outputs_table(tx, fmt))
