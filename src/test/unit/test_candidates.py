"""
Unit tests for Candidate objects
"""
from collections import Counter
from datetime import datetime as dt
from json import dumps
from statistics import median, mean

import pytest
from bobs.obs.candidates import Candidate, TransactionV3
from bobs.obs.criteria import Criterion

EXAMPLE_RAW_DATA = {'test': 'data'}


def test_wrapping() -> None:
    candidate = Candidate(EXAMPLE_RAW_DATA)
    assert candidate.raw_data['test'] == 'data'
    assert candidate['test'] == 'data'
    assert candidate.test == 'data'
    assert 'test' in candidate
    assert 'test' in candidate.raw_data
    assert 'data' not in candidate
    assert 'data' not in candidate.raw_data
    # Explicitly tests against **json**.loads() rather than orjson, for compatibility testing
    assert str(candidate) == dumps(EXAMPLE_RAW_DATA).replace(' ', '')


def test_call() -> None:
    """
    Only a simple check here, the actual testing of this is in the functional tests.
    """
    candidate = Candidate(EXAMPLE_RAW_DATA)
    assert isinstance(candidate({}), bool)


def test_match_criterion() -> None:
    """
    We replace an actual Criterion with a fake one, and only stress test that
    this method does the expected thing.
    """

    class FakeCriterion(Criterion):
        def __call__(self, candidate_: Candidate) -> bool:
            """
            True for the id_ found path, False if the entire Candidate is used as value.
            """
            return isinstance(candidate_, str)

    candidate = Candidate(EXAMPLE_RAW_DATA)
    fake_criterion = FakeCriterion()
    assert isinstance(candidate.match_criterion('', fake_criterion), bool)
    assert candidate.match_criterion('test', fake_criterion) is True
    assert candidate.match_criterion('not_found', fake_criterion) is False


def test_transaction(tx_candidate) -> None:
    # Test inputs
    inputs = tx_candidate.inputs
    input1 = next(inputs)
    assert isinstance(input1, dict)
    assert input1['txid'] == 'a525c3c37b4bf5d5bd8515901dbd1085ab259788471ae3124165ad53de2c3937'
    with pytest.raises(StopIteration):
        next(inputs)
    # Test outputs
    outputs = tx_candidate.outputs
    output1 = next(outputs)
    assert isinstance(output1, dict)
    assert output1['n'] == 0
    assert output1['value'] == 0.0
    output2 = next(outputs)
    assert output2['n'] == 1
    assert output2['value'] == 0.00047977
    with pytest.raises(StopIteration):
        next(outputs)
    # Test is coinbase
    assert not tx_candidate.is_coinbase
    # Test iterator of output values
    output_values = tx_candidate.out_values
    value1 = next(output_values)
    assert value1 == 0
    value2 = next(output_values)
    assert value2 == 0.00047977
    with pytest.raises(StopIteration):
        next(output_values)
    # Test sum of all output values
    assert tx_candidate.total_out == round(0 + 0.00047977, 8)
    # Test number of inputs
    assert tx_candidate.n_in == 1
    # Test number of outputs
    assert tx_candidate.n_out == 2
    # Test output values counter
    assert tx_candidate.out_counter == Counter((0, 0.00047977))
    # Test the most frequent equal output value
    assert tx_candidate.n_eq == 1
    # Test the denomination of the most frequent equal output value.
    # There are no equal outputs here.
    assert tx_candidate.den == 0
    # Test date
    assert dt.utcfromtimestamp(tx_candidate['timestamp_date']).strftime('%Y-%m-%d %H:%M') == tx_candidate.date
    # Test iterator of output addresses
    out_addrs = tx_candidate.out_addrs
    addr1 = next(out_addrs)
    # First output is OP RETURN, so no address.
    assert addr1 == ''
    addr2 = next(out_addrs)
    assert addr2 == 'bc1q3tycwywq4zu0dfpjq6d8xge05slqyjrn2p58hy'
    with pytest.raises(StopIteration):
        next(out_addrs)
    # Test iterator of output types
    out_types = tx_candidate.out_types
    type1 = next(out_types)
    # OP RETURN is nulldata
    assert type1 == 'nulldata'
    type2 = next(out_types)
    assert type2 == 'witness_v0_keyhash'
    with pytest.raises(StopIteration):
        next(out_types)


def test_transactionv3(txv3: TransactionV3) -> None:
    # Test iterator of input values
    input_values = txv3.in_values
    value1 = next(input_values)
    assert value1 == 4.58794295
    with pytest.raises(StopIteration):
        next(input_values)
    # Test sum of all input values
    assert txv3.total_in == round(4.58794295, 8)
    assert txv3.abs_fee == 0.001
    assert txv3.rel_fee == round(0.001 * 1e8 / txv3.vsize, 1)
    # Test input values counter
    assert txv3.in_counter == Counter((4.58794295,))
    # Test iterator of input addresses
    in_addrs = txv3.in_addrs
    addr1 = next(in_addrs)
    assert addr1 == '17A16QmavnUfCW11DAApiJxp7ARnxN5pGX'
    with pytest.raises(StopIteration):
        next(in_addrs)
    # Test iterator of all addresses
    addrs = txv3.addresses
    addr1 = next(addrs)
    assert addr1 == '17A16QmavnUfCW11DAApiJxp7ARnxN5pGX'
    addr2 = next(addrs)
    assert addr2 == '3J4fKq3ehrD4kyvtB6ckiu7nXWNMGZ6Usb'
    addr3 = next(addrs)
    assert addr3 == '3AYjDZsEc4Ax59oBgda2nm2TJH7igfD2m1'
    addr4 = next(addrs)
    assert addr4 == '17A16QmavnUfCW11DAApiJxp7ARnxN5pGX'
    with pytest.raises(StopIteration):
        next(addrs)
    # Test iterator of input types
    in_types = txv3.in_types
    type1 = next(in_types)
    assert type1 == 'pubkeyhash'
    with pytest.raises(StopIteration):
        next(in_types)
    # Test iterator of all types
    types = txv3.types
    type1 = next(types)
    assert type1 == 'pubkeyhash'
    type2 = next(types)
    assert type2 == 'scripthash'
    type3 = next(types)
    assert type3 == 'scripthash'
    type4 = next(types)
    assert type4 == 'pubkeyhash'


def test_block(block_candidate) -> None:
    # Test txs, Block with no details only return TXIDs
    txs = block_candidate.txs
    tx1 = next(txs)
    assert isinstance(tx1, str)
    assert tx1 == 'eb495e3b9c09f91f1b86f9bc7517d82b9710fbeaf973b5e859d617abf770e84a'
    tx2 = next(txs)
    assert isinstance(tx2, str)
    assert tx2 == '1cc7a992f7e3b62f775330cd8f94f7440fb5d9247b40c2147a2fa680365c16f4'
    tx3 = next(txs)
    assert isinstance(tx3, str)
    assert tx3 == '089d0cbaead4f2d4c3840d7702c8889ccb6660e88194161f8797d5becab98610'
    with pytest.raises(StopIteration):
        next(txs)
    # Test date
    assert dt.utcfromtimestamp(block_candidate['time']).strftime('%Y-%m-%d %H:%M') == block_candidate.date


def test_blockv3(blockv3_candidate) -> None:
    # Test txs, Block with details return TransactionV3 candidates.
    txs = blockv3_candidate.txs
    tx1 = next(txs)
    assert isinstance(tx1, TransactionV3)
    assert tx1.is_coinbase
    assert tx1.txid == 'eb495e3b9c09f91f1b86f9bc7517d82b9710fbeaf973b5e859d617abf770e84a'
    tx2 = next(txs)
    assert isinstance(tx2, TransactionV3)
    assert tx2.txid == '1cc7a992f7e3b62f775330cd8f94f7440fb5d9247b40c2147a2fa680365c16f4'
    tx3 = next(txs)
    assert isinstance(tx3, TransactionV3)
    assert tx3.txid == '089d0cbaead4f2d4c3840d7702c8889ccb6660e88194161f8797d5becab98610'
    # Test the total number of inputs in the block
    assert blockv3_candidate.n_in == 3
    # Test the total number of outputs in the block
    assert blockv3_candidate.n_out == 8
    # Test the absolute fees iterator
    abs_fees = blockv3_candidate.abs_fees
    fee1 = next(abs_fees)
    # The first transaction in a block is always a coinbase.
    assert fee1 == 0
    fee2 = next(abs_fees)
    assert fee2 == 0.001
    fee3 = next(abs_fees)
    assert fee3 == 0.0004775
    with pytest.raises(StopIteration):
        next(abs_fees)
    # Test the relative fees iterator
    rel_fees = blockv3_candidate.rel_fees
    fee1 = next(rel_fees)
    # The first transaction in a block is always a coinbase.
    assert fee1 == 0
    fee2 = next(rel_fees)
    assert fee2 == round(0.001 * 1e8 / blockv3_candidate.tx[1]['vsize'], 1)
    fee3 = next(rel_fees)
    assert fee3 == round(0.0004775 * 1e8 / blockv3_candidate.tx[2]['vsize'], 1)
    with pytest.raises(StopIteration):
        next(rel_fees)
    # Test the sum of all absolute fees in the block.
    assert blockv3_candidate.total_fee == 0 + 0.001 + 0.0004775
    # Test the median of all absolute fees in the block.
    assert blockv3_candidate.median_fee == median((0, 0.001, 0.0004775))
    # Test the mean of all absolute fees in the block.
    assert blockv3_candidate.mean_fee == mean((0, 0.001, 0.0004775))
    # Test the median of all relative fees in the block.
    assert blockv3_candidate.median_rel_fee == median((fee1, fee2, fee3))
    # Test the mean of all relative fees in the block.
    assert blockv3_candidate.mean_rel_fee == mean((fee1, fee2, fee3))
    # Test the sum of all inputs UTXOs
    assert blockv3_candidate.total_in == 0 + 4.58794295 + 0.71996206
    # Test the sum of all inputs UTXOs
    assert blockv3_candidate.total_out == round(
        6.33776205 + 0.0 + 0.0 + 0.15553898 + 2.5 + 1.93140397 + 0.0075038 + 0.71198076,
        8)
