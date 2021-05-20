from typing import Iterable, Dict, Tuple

from pandas import DataFrame

TX_DICT_KEYS: Tuple[str, ...] = ('txid', 'version', 'size', 'vsize', 'weight', 'locktime', 'n_in', 'n_out',
                                 'n_eq', 'den', 'abs_fee', 'rel_fee', 'height', 'date', 'inputs', 'outputs')

TX_KEY_DTYPES: Dict[str, str] = {
    'txid': 'object',
    'version': 'uint8',
    'size': 'uint32',
    'vsize': 'uint32',
    'weight': 'uint32',
    'locktime': 'uint32',
    'inputs': 'object',
    'n_in': 'uint16',
    'outputs': 'object',
    'n_out': 'uint16',
    'n_eq': 'uint16',
    'den': 'uint64',
    'abs_fee': 'uint32',
    'rel_fee': 'uint16',
    'height': 'uint32',
    'date': 'datetime64[ns]',
    'inputs_sum': 'uint64',
    'outputs_sum': 'uint64',
    'coinbase': 'bool',
}


def convert_dtypes(df: DataFrame, keys: Iterable[str]) -> DataFrame:
    """
    Wrapper around df.astype(), cast DataFrame columns to the appropriate type for each key.
    Use mapping from TX_KEY_DTYPES global.
    """
    return df.astype({key: TX_KEY_DTYPES[key] for key in keys}, copy=False)
