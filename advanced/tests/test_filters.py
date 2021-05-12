import inspect
import os
import sys
from collections import namedtuple

import template_txs

# Used to import from parent directory
# TODO
# Consider turning it into a package
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import filters
import containers

simple_object = namedtuple('simple_object', ['criteria1'])
date_dict = {'date': ''}
simple_tx = containers.Tx(template_txs.simple_transaction, 1600362598, 625000000, 648775)
coinbase_tx = containers.Tx(template_txs.coinbase_transaction, 1600362598, 625000000, 648775)
same_output_type_tx = containers.Tx(template_txs.same_output_type_tx, 1600456080, 625000000, 648958)
jm_tx = containers.Tx(template_txs.joinmarket_transaction, 1615530893, 625000000, 674250)


def test_match_txid():
    # Test TxFilter with txid criteria
    f = filters.TxFilter(txid='dde13831553ccfc48fb6ef3237ebea81a87ab67de53ed5d6476d44d61a6d37cc')
    assert f.match(simple_tx)
    # Test custom made TxidFilter
    f = filters.TxidFilter('dde13831553ccfc48fb6ef3237ebea81a87ab67de53ed5d6476d44d61a6d37cc')
    assert f.match(simple_tx)
    # Test wrong TXID
    f = filters.TxFilter(txid='wrongtxid')
    assert not f.match(simple_tx)
    f = filters.TxidFilter('wrongtxid')
    assert not f.match(simple_tx)
    # Test it works with only a fraction of the whole TXID
    f = filters.TxFilter(txid='dde1383')
    assert f.match(simple_tx)
    f = filters.TxidFilter('dde1383')
    assert f.match(simple_tx)


def test_match_hash() -> None:
    f = filters.TxFilter(hash='9a47c3bee0e4327b7587918a614ecb7c59c5882de005cbf718c3611ced26357d')
    assert f.match(simple_tx)
    # Test wrong hash
    f = filters.TxFilter(hash='wronghash')
    assert not f.match(simple_tx)
    # Test it works with only a fraction of the whole hash
    f = filters.TxFilter(hash='47c3be')
    assert f.match(simple_tx)


def test_match_version() -> None:
    f = filters.TxFilter(version=[1, 1])
    assert f.match(simple_tx)
    f = filters.TxFilter(version=[0, 2])
    assert f.match(simple_tx)
    # Test wrong version
    f = filters.TxFilter(version=[0, 0])
    assert not f.match(simple_tx)
    f = filters.TxFilter(version=[2, 2])
    assert not f.match(simple_tx)


def test_match_size() -> None:
    f = filters.TxFilter(size=[249, 249])
    assert f.match(simple_tx)
    f = filters.TxFilter(size=[0, 300])
    assert f.match(simple_tx)
    # Test wrong size
    f = filters.TxFilter(size=[0, 248])
    assert not f.match(simple_tx)
    f = filters.TxFilter(size=[250, 300])
    assert not f.match(simple_tx)


def test_match_vsize() -> None:
    f = filters.TxFilter(vsize=[168, 168])
    assert f.match(simple_tx)
    f = filters.TxFilter(vsize=[0, 300])
    assert f.match(simple_tx)
    # Test wrong vsize
    f = filters.TxFilter(vsize=[0, 167])
    assert not f.match(simple_tx)
    f = filters.TxFilter(vsize=[169, 300])
    assert not f.match(simple_tx)


def test_match_weight() -> None:
    f = filters.TxFilter(weight=[669, 669])
    assert f.match(simple_tx)
    f = filters.TxFilter(weight=[0, 1000])
    assert f.match(simple_tx)
    # Test wrong weight
    f = filters.TxFilter(weight=[0, 668])
    assert not f.match(simple_tx)
    f = filters.TxFilter(weight=[670, 100])
    assert not f.match(simple_tx)


def test_match_locktime() -> None:
    f = filters.TxFilter(locktime=[0, 0])
    assert f.match(simple_tx)
    f = filters.TxFilter(locktime=[0, 1000])
    assert f.match(simple_tx)
    # Test wrong locktime
    f = filters.TxFilter(locktime=[1, 668])
    assert not f.match(simple_tx)


def test_match_n_in() -> None:
    f = filters.TxFilter(n_in=[1, 1])
    assert f.match(simple_tx)
    f = filters.TxFilter(n_in=[0, 10])
    assert f.match(simple_tx)
    # Test wrong n_in
    f = filters.TxFilter(n_in=[0, 0])
    assert not f.match(simple_tx)
    f = filters.TxFilter(n_in=[2, 3])
    assert not f.match(simple_tx)


def test_match_n_out() -> None:
    f = filters.TxFilter(n_out=[2, 2])
    assert f.match(simple_tx)
    f = filters.TxFilter(n_out=[0, 10])
    assert f.match(simple_tx)
    # Test wrong n_in
    f = filters.TxFilter(n_out=[0, 1])
    assert not f.match(simple_tx)
    f = filters.TxFilter(n_out=[3, 5])
    assert not f.match(simple_tx)


def test_match_n_eq() -> None:
    f = filters.TxFilter(n_eq=[7, 7])
    assert f.match(jm_tx)
    f = filters.TxFilter(n_eq=[1, 10])
    assert f.match(jm_tx)
    # Test wrong n_eq
    f = filters.TxFilter(n_eq=[1, 6])
    assert not f.match(jm_tx)
    f = filters.TxFilter(n_eq=[8, 12])
    assert not f.match(jm_tx)


def test_match_den() -> None:
    f = filters.TxFilter(den=(4116232, 4116232))
    assert f.match(jm_tx)
    f = filters.TxFilter(den=(0, 4116232))
    assert f.match(jm_tx)
    # Test wrong denomination
    f = filters.TxFilter(den=(0, 4116231))
    assert not f.match(jm_tx)
    f = filters.TxFilter(den=(4116233, 54116232))
    assert not f.match(jm_tx)


def test_match_address():
    # Test TxFilter with address criteria
    f = filters.TxFilter(address='3NG7EZRcHpmaGzJkopBUbiTqSvDfJmX4eo')
    assert f.match(simple_tx)
    # Test custom made AddressFilter
    f = filters.AddressFilter('3NG7EZRcHpmaGzJkopBUbiTqSvDfJmX4eo')
    assert f.match(simple_tx)
    # Test wrong address
    f = filters.TxFilter(address='wrongaddress')
    assert not f.match(simple_tx)
    f = filters.AddressFilter('wrongaddress')
    assert not f.match(simple_tx)
    # Test it works with only a fraction of the whole TXID
    f = filters.TxFilter(address='zJkop')
    assert f.match(simple_tx)
    f = filters.AddressFilter('zJkop')
    assert f.match(simple_tx)


def test_match_in_type() -> None:
    f = filters.TxFilter(in_type='scripthash')
    assert f.match(simple_tx)
    f = filters.TxFilter(in_type='wrongtype')
    assert not f.match(simple_tx)


def test_match_out_type() -> None:
    f = filters.TxFilter(out_type='scripthash')
    assert not f.match(simple_tx)
    f = filters.TxFilter(out_type='scripthash')
    assert f.match(same_output_type_tx)


def test_match_coinbase() -> None:
    # Test TxFilter with coinbase criteria
    f = filters.TxFilter(coinbase=True)
    assert f.match(coinbase_tx)
    f = filters.TxFilter(coinbase=False)
    assert not f.match(coinbase_tx)
    # Test custom made CoinbaseFilter
    f = filters.CoinbaseFilter()
    assert f.match(coinbase_tx)
    # Test not coinbase
    f = filters.TxFilter(coinbase=True)
    assert not f.match(simple_tx)
    f = filters.TxFilter(coinbase=False)
    assert f.match(simple_tx)
    f = filters.CoinbaseFilter()
    assert not f.match(simple_tx)


def test_callables() -> None:
    def my_callable(tx: containers.Tx) -> bool:
        return tx.vsize + tx.weight == 837

    f = filters.Filter(callables=[my_callable])
    assert f.match(simple_tx)
    assert not f.match(coinbase_tx)


def test_coinjoin_filter() -> None:
    f = filters.CjFilter()
    assert f.match(jm_tx)


def test_joinmarket_filter() -> None:
    f = filters.JoinmarketFilter()
    assert f.match(jm_tx)
