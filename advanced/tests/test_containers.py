import inspect
import os
import sys
from typing import List

import template_txs

# Used to import from parent directory
# TODO
# Consider turning it into a package
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from containers import Tx, TxInput, TxOutput

simple_tx_addresses: List[str] = ['3NG7EZRcHpmaGzJkopBUbiTqSvDfJmX4eo', '1HWaDbvKnK2qwsRDmHMVg6yQA9hgb2ALNH',
                                  '3HEr6PeqQaeqi2w4qTriydAqJ2aLQ2Y4yz']
coinbase_tx_addresses: List[str] = ['126W33f3fJaVzPT57pVFBZZt7PUCTHnH7J']

simple_tx_types: List[str] = ['scripthash', 'pubkeyhash', 'scripthash']
coinbase_tx_types: List[str] = ['coinbase', 'pubkeyhash', 'nulldata', 'nulldata', 'nulldata']


def test_simple_tx() -> None:
    tx = Tx(template_txs.simple_transaction, 1600362598, 625000000, 648775)
    assert tx.txid == 'dde13831553ccfc48fb6ef3237ebea81a87ab67de53ed5d6476d44d61a6d37cc'
    assert tx.version == 1
    assert tx.size == 249
    assert tx.vsize == 168
    assert tx.weight == 669
    assert tx.locktime == 0
    assert isinstance(tx.inputs[0], TxInput)
    assert isinstance(tx.outputs[0], TxOutput)
    assert tx.inputs[0].txid == '51380e6d281e942eb2fd7109cd6a72799a9640e17f24034d96c4a9f4704cd29b'
    assert tx.inputs[0].height == 648563
    assert tx.inputs[0].value == 217370429
    assert tx.inputs[0].vout == 1
    assert tx.inputs[0].addresses == ['3NG7EZRcHpmaGzJkopBUbiTqSvDfJmX4eo']
    assert tx.inputs[0].type == 'scripthash'
    assert tx.n_in == 1
    assert tx.outputs[0].value == 922158
    assert tx.outputs[1].value == 216317735
    assert tx.outputs[0].vout == 0
    assert tx.outputs[1].vout == 1
    assert tx.outputs[0].addresses == ['1HWaDbvKnK2qwsRDmHMVg6yQA9hgb2ALNH']
    assert tx.outputs[1].addresses == ['3HEr6PeqQaeqi2w4qTriydAqJ2aLQ2Y4yz']
    assert tx.outputs[0].type == 'pubkeyhash'
    assert tx.outputs[1].type == 'scripthash'
    assert tx.n_out == 2
    assert tx.n_eq == 1
    assert tx.den == 0
    assert tx.abs_fee == 130536
    assert tx.rel_fee == 777
    assert tx.height == 648775
    assert tx.date == '2020-09-17 17:09'
    assert tx.coinbase is False
    # Test __getitem__ dunder method
    assert tx.timestamp_date == 1600362598
    assert tx['date'] == '2020-09-17 17:09'
    assert list(tx.addresses) == simple_tx_addresses
    assert list(tx.types) == simple_tx_types


def test_coinbase_tx() -> None:
    tx = Tx(template_txs.coinbase_transaction, 1600362598, 625000000, 648775)
    assert tx.txid == 'aefaf56793980778f4ed2d5d1900a4e99a9029966b0897ae35ad3d6c6a6d1e5d'
    assert tx.version == 1
    assert tx.size == 362
    assert tx.vsize == 335
    assert tx.weight == 1340
    assert tx.locktime == 2192709790
    assert isinstance(tx.inputs[0], TxInput)
    assert isinstance(tx.outputs[0], TxOutput)
    assert tx.inputs[0].txid == '0347e609046998635f2f706f6f6c696e2e636f6d2ffabe6d6d092f11a0c31abafdc2ecf84f0aedd3745a6ce7e38d139dabc350f0822caa6500010000000000000013d3f5221eab97eaca195f9135a260ca118042487c00d10e000000000000'
    assert tx.inputs[0].height is None
    assert tx.inputs[0].value == 625000000
    assert tx.inputs[0].vout is None
    assert tx.inputs[0].addresses == []
    assert tx.inputs[0].type == 'coinbase'
    assert tx.n_in == 1
    assert tx.outputs[0].value == 707505391
    assert tx.outputs[1].value == 0
    assert tx.outputs[2].value == 0
    assert tx.outputs[3].value == 0
    assert tx.outputs[0].vout == 0
    assert tx.outputs[1].vout == 1
    assert tx.outputs[2].vout == 2
    assert tx.outputs[3].vout == 3
    assert tx.outputs[0].addresses == ['126W33f3fJaVzPT57pVFBZZt7PUCTHnH7J']
    assert tx.outputs[1].addresses == []
    assert tx.outputs[2].addresses == []
    assert tx.outputs[3].addresses == []
    assert tx.outputs[0].type == 'pubkeyhash'
    assert tx.outputs[1].type == 'nulldata'
    assert tx.outputs[2].type == 'nulldata'
    assert tx.outputs[3].type == 'nulldata'
    assert tx.n_out == 4
    assert tx.n_eq == 3
    assert tx.den == 0
    assert tx.abs_fee == 0
    assert tx.rel_fee == 0
    assert tx.height == 648775
    assert tx.timestamp_date == 1600362598
    assert tx.date == '2020-09-17 17:09'
    assert tx.coinbase is True
    assert list(tx.addresses) == coinbase_tx_addresses
    assert list(tx.types) == coinbase_tx_types


def test_joinmarket_tx() -> None:
    tx = Tx(template_txs.joinmarket_transaction, 1615530893, 625000000, 674250)
    assert tx.n_eq == 7
    assert tx.den == 4116232
    assert tx.abs_fee == 156383
    assert tx.rel_fee == 134.7
