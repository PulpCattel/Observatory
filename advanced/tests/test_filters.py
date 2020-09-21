import inspect
import os
import pytest
import sys
import template_txs
from collections import namedtuple

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import filters
import containers

simple_object = namedtuple('obj', ['criteria1'])
date_dict = {'date': ''}
simple_tx = containers.Tx(template_txs.simple_transaction, 1600362598, 625000000, 648775)
coinbase_tx = containers.Tx(template_txs.coinbase_transaction, 1600362598, 625000000, 648775)
same_output_type_tx = containers.Tx(template_txs.same_output_type_tx, 1600456080, 625000000, 648958)


# Test Filter


def test_match_attr():
    f = filters.Filter(criteria1=(10, 20))
    obj = simple_object(2)
    assert not f.match(obj)
    obj = simple_object(10)
    assert f.match(obj)
    obj = simple_object(20)
    assert f.match(obj)
    obj = simple_object(21)
    assert not f.match(obj)
    # Test dates
    f = filters.Filter(date=('2020-09-17 17', '2020-09-17 18'))
    date_dict['date'] = '2020-09-17 17:09'
    assert f.match(date_dict)
    date_dict['date'] = '2020-09-18 22:00'
    assert not f.match(date_dict)
    f = filters.Filter(date=('2020', '2021'))
    assert f.match(date_dict)
    f = filters.Filter(date=('2021', '2022'))
    assert not f.match(date_dict)


# Test TxFilter

def test_match_txid():
    f = filters.TxFilter(txid='dde13831553ccfc48fb6ef3237ebea81a87ab67de53ed5d6476d44d61a6d37cc')
    assert f.match(simple_tx)
    # Test custom made txid filter
    f = filters.TxidTxFilter('dde13831553ccfc48fb6ef3237ebea81a87ab67de53ed5d6476d44d61a6d37cc')
    assert f.match(simple_tx)
    f = filters.TxidTxFilter('wrongtxid')
    assert not f.match(simple_tx)
    f = filters.TxidTxFilter('dde1383')
    assert f.match(simple_tx)


def test_match_addr():
    f = filters.TxFilter(address=['3NG7EZRcHpmaGzJkopBUbiTqSvDfJmX4eo'])
    assert f.match(simple_tx)
    f = filters.TxFilter(address=['wrongaddress'])
    assert not f.match(simple_tx)
    f = filters.TxFilter(address=['3NG7EZRcHpmaG', 'zJkopBUbiTqSvDfJmX4eo'])
    assert f.match(simple_tx)
    f = filters.TxFilter(address=['3NG7EZRcHpmaG', 'wrongaddress'])
    assert not f.match(simple_tx)
    # Test custom made address filter
    f = filters.AddressTxFilter('3NG7EZRcHpmaGzJkopBUbiTqSvDfJmX4eo')
    assert f.match(simple_tx)
    f = filters.AddressTxFilter('wrongaddress')
    assert not f.match(simple_tx)
    f = filters.AddressTxFilter('3NG7EZRcHpmaG', 'zJkopBUbiTqSvDfJmX4eo')
    assert f.match(simple_tx)
    f = filters.AddressTxFilter('3NG7EZRcHpmaG', 'wrongaddress')
    assert not f.match(simple_tx)


def test_match_in_type():
    f = filters.TxFilter(in_type='scripthash')
    assert f.match(simple_tx)
    f = filters.TxFilter(in_type='wrongtype')
    assert not f.match(simple_tx)
    f = filters.CoinbaseTxFilter()
    assert not f.match(simple_tx)
    assert f.match(coinbase_tx)


def test_match_out_type():
    f = filters.TxFilter(out_type='wrongtype')
    assert not f.match(simple_tx)
    f = filters.TxFilter(out_type='scripthash')
    assert f.match(same_output_type_tx)


def test_functions_criteria():
    def test_function(tx):
        if tx.vsize + tx.weight == 837:
            return True
        return False

    f = filters.TxFilter(callables=[test_function])
    assert f.match(simple_tx)
    assert not f.match(coinbase_tx)
