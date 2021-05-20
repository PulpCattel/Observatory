from inspect import getfile, currentframe
from os import path
from sys import path as sys_path

from pandas import DataFrame

from template_txs import simple_transaction

# Used to import from parent directories
currentdir = path.dirname(path.abspath(getfile(currentframe())))
parentdir = path.dirname(currentdir)
sys_path.insert(0, parentdir)

from pandas_utils import convert_dtypes, TX_KEY_DTYPES
from containers import Tx


def test_convert_dtype():
    df = DataFrame([Tx(simple_transaction, 100, 100).dict(TX_KEY_DTYPES.keys())])
    assert len(df) == 1
    assert isinstance(df, DataFrame)
    assert df['version'].dtype == 'int64'
    df = convert_dtypes(df, TX_KEY_DTYPES.keys())
    assert len(df) == 1
    assert isinstance(df, DataFrame)
    for key in df:
        assert df[key].dtype == TX_KEY_DTYPES[key]
