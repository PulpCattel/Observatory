from collections import Counter

from bobs.bitcoin.containers import Tx, TxInput, TxOutput
from bobs.tests import data

SIMPLE_TX_IN_ADDRS = ['bc1qwqdg6squsna38e46795at95yu9atm8azzmyvckulcc7kytlcckxswvvzej']
SIMPLE_TX_OUT_ADDRS = ['18ccrRpt4Va9VwD9ttaZT3LVN9wcugfp6h',
                       'bc1qwqdg6squsna38e46795at95yu9atm8azzmyvckulcc7kytlcckxswvvzej']
SIMPLE_TX_IN_TYPES = ['witness_v0_scripthash']
SIMPLE_TX_OUT_TYPES = ['pubkeyhash', 'witness_v0_scripthash']


def test_simple_tx():
    tx = Tx(data.SIMPLE_TX, 1600362598, 648775)
    assert tx.txid == data.SIMPLE_TX['txid']
    assert tx.hash == data.SIMPLE_TX['hash']
    assert tx.version == data.SIMPLE_TX['version']
    assert tx.size == data.SIMPLE_TX['size']
    assert tx.vsize == data.SIMPLE_TX['vsize']
    assert tx.weight == data.SIMPLE_TX['weight']
    assert tx.locktime == data.SIMPLE_TX['locktime']
    assert isinstance(tx.inputs, list)
    assert isinstance(tx.outputs, list)
    assert all(isinstance(input_, TxInput) for input_ in tx.inputs)
    assert isinstance(tx.inputs[0].outpoint, str)
    assert tx.inputs[0].txid == data.SIMPLE_TX['vin'][0]['txid']
    assert tx.inputs[0].prevout.vout == data.SIMPLE_TX['vin'][0]['vout']
    assert tx.inputs[0].height == data.SIMPLE_TX['vin'][0]['prevout']['height']
    assert tx.inputs[0].script_sig == data.SIMPLE_TX['vin'][0]['scriptSig']['asm']
    assert isinstance(tx.inputs[0].prevout, TxOutput)
    assert tx.inputs[0].prevout.value == data.SIMPLE_TX['vin'][0]['prevout']['value'] * 1e8
    assert tx.inputs[0].prevout.vout == data.SIMPLE_TX['vin'][0]['vout']
    assert isinstance(tx.inputs[0].prevout.script, str)
    assert tx.inputs[0].prevout.script == data.SIMPLE_TX['vin'][0]['prevout']['scriptPubKey']['asm']
    assert tx.inputs[0].prevout.address == data.SIMPLE_TX['vin'][0]['prevout']['scriptPubKey']['address']
    assert isinstance(tx.inputs[0].prevout.type, str)
    assert tx.inputs[0].prevout.type == 'witness_v0_scripthash'
    assert tx.inputs[0].sequence == data.SIMPLE_TX['vin'][0]['sequence']
    assert tx.inputs[0].txinwitness == data.SIMPLE_TX['vin'][0]['txinwitness']
    assert tx.n_in == len(data.SIMPLE_TX['vin'])
    assert all(isinstance(output, TxOutput) for output in tx.outputs)
    assert tx.outputs[0].value == data.SIMPLE_TX['vout'][0]['value'] * 1e8
    assert tx.outputs[1].value == data.SIMPLE_TX['vout'][1]['value'] * 1e8
    assert tx.outputs[0].vout == data.SIMPLE_TX['vout'][0]['n']
    assert tx.outputs[1].vout == data.SIMPLE_TX['vout'][1]['n']
    assert isinstance(tx.outputs[0].script, str)
    assert tx.outputs[0].script == data.SIMPLE_TX['vout'][0]['scriptPubKey']['asm']
    assert tx.outputs[0].address == data.SIMPLE_TX['vout'][0]['scriptPubKey']['address']
    assert tx.outputs[0].type == 'pubkeyhash'
    assert isinstance(tx.outputs[1].script, str)
    assert tx.outputs[1].script == data.SIMPLE_TX['vout'][1]['scriptPubKey']['asm']
    assert tx.outputs[1].address == data.SIMPLE_TX['vout'][1]['scriptPubKey']['address']
    assert tx.outputs[1].type == 'witness_v0_scripthash'
    assert tx.n_out == len(data.SIMPLE_TX['vout'])
    assert tx.n_eq == 1
    assert tx.den == 0
    assert tx.abs_fee == data.SIMPLE_TX['fee'] * 1e8
    assert tx.rel_fee == round(data.SIMPLE_TX['fee'] * 1e8 / data.SIMPLE_TX['vsize'], 1)
    # Fake height and date
    assert tx.height == 648775
    assert tx.date == '2020-09-17 17:09'
    assert tx.is_coinbase is False
    # Test __getitem__ dunder method
    assert tx.timestamp_date == 1600362598
    assert tx['date'] == '2020-09-17 17:09'
    # Test properties
    assert tx.inputs_sum == sum(input_['prevout']['value'] * 1e8 for input_ in data.SIMPLE_TX['vin'])
    assert tx.outputs_sum == sum(output['value'] * 1e8 for output in data.SIMPLE_TX['vout'])
    assert list(tx.in_addrs) == SIMPLE_TX_IN_ADDRS
    assert list(tx.out_addrs) == SIMPLE_TX_OUT_ADDRS
    assert tx.in_counter == Counter(input_['prevout']['value'] * 1e8 for input_ in data.SIMPLE_TX['vin'])
    assert tx.out_counter == Counter(output['value'] * 1e8 for output in data.SIMPLE_TX['vout'])
    assert list(tx.in_types) == SIMPLE_TX_IN_TYPES
    assert list(tx.out_types) == SIMPLE_TX_OUT_TYPES
    assert list(tx.input_values) == list(input_['prevout']['value'] * 1e8 for input_ in data.SIMPLE_TX['vin'])
    assert list(tx.output_values) == list(output['value'] * 1e8 for output in data.SIMPLE_TX['vout'])


def test_coinbase_tx():
    tx = Tx(data.COINBASE_TX, 1600362598, 648775)
    assert tx.is_coinbase
    assert tx.inputs[0].script_sig == data.COINBASE_TX['vin'][0]['coinbase']
    assert tx.inputs[0].sequence == data.COINBASE_TX['vin'][0]['sequence']
    assert tx.inputs[0].outpoint is None
    assert tx.inputs[0].height is None
    assert tx.inputs[0].prevout is None
    assert tx.inputs[0].txinwitness is None
    assert tx.abs_fee == 0
    assert tx.rel_fee == 0
    assert list(tx.in_addrs) == []
    assert list(tx.in_counter) == []
    assert list(tx.in_types) == []
    assert list(tx.input_values) == []
