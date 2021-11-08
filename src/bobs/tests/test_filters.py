"""
Test Criteria and Filters
"""
from re import compile as re_compile

from _pytest.python_api import raises
from bobs.bitcoin.containers import Tx
from bobs.obs.filters import CriterionField, Greater, Regex, TxFilter, Include, Equal, Different, Lesser, Between, \
    Appear, Satisfy
from bobs.tests.data import SIMPLE_TX
from hypothesis import given, strategies as st
from marshmallow import ValidationError


@given(st.integers(), st.integers())
def test_greater(value, candidate):
    greater = Greater(value)
    if candidate >= value:
        assert greater(candidate)
    if candidate < value:
        assert not greater(candidate)
    greater = Greater(value, inclusive=False)
    if candidate > value:
        assert greater(candidate)
    if candidate <= value:
        assert not greater(candidate)


@given(st.integers(), st.integers())
def test_lesser(value, candidate):
    lesser = Lesser(value)
    if candidate <= value:
        assert lesser(candidate)
    if candidate > value:
        assert not lesser(candidate)
    lesser = Lesser(value, inclusive=False)
    if candidate < value:
        assert lesser(candidate)
    if candidate >= value:
        assert not lesser(candidate)


@given(st.integers(), st.integers(), st.integers())
def test_between(min_, max_, candidate):
    between = Between(min_, max_)
    if min_ <= candidate <= max_:
        assert between(candidate) is True
    else:
        assert between(candidate) is False
    between = Between(min_, max_, inclusive=False)
    if min_ < candidate < max_:
        assert between(candidate) is True
    else:
        assert between(candidate) is False


@given(st.text(), st.text())
def test_equal(value, candidate):
    equal = Equal(value)
    if candidate == value:
        assert equal(candidate) is True
    else:
        assert equal(candidate) is False


@given(st.text(), st.text())
def test_different(value, candidate):
    different = Different(value)
    if candidate != value:
        assert different(candidate) is True
    else:
        assert different(candidate) is False


@given(st.data())
def test_include(data):
    value = data.draw(st.one_of(st.integers(), st.text()))
    include = Include(value)
    if isinstance(value, int):
        candidate = data.draw(st.one_of(st.lists(st.integers()), st.sets(st.integers())))
    else:
        candidate = data.draw(st.text())
    if value in candidate:
        assert include(candidate) is True
    else:
        assert include(candidate) is False


@given(st.one_of(st.text(), st.lists(st.text())), st.text())
def test_appear(value, candidate):
    appear = Appear(value)
    if candidate in value:
        assert appear(candidate) is True
    else:
        assert appear(candidate) is False


@given(st.integers())
def test_satisfy(candidate):
    def example_callable(num: int) -> int:
        return num + 1 == 1

    satisfy = Satisfy(example_callable)
    if example_callable(candidate):
        assert satisfy(candidate) is True
    else:
        assert satisfy(candidate) is False


@given(st.text())
def test_regex(candidate):
    value = r'\d'
    pattern = re_compile(value)
    regex = Regex(value)
    if pattern.search(candidate) is not None:
        assert regex(candidate)
    else:
        assert not regex(candidate)


def test_restricted_eval():
    forbidden_string = "len([1, 2, 3])"
    with raises(ValidationError):
        CriterionField._restricted_eval(forbidden_string)
    forbidden_string = "''.__class__"
    with raises(ValidationError):
        CriterionField._restricted_eval(forbidden_string)
    accepted_string = "Greater(5)"
    assert Greater(5) == CriterionField._restricted_eval(accepted_string)


def test_tx_filter():
    tx = Tx(SIMPLE_TX, 1000, 1000)
    tx_filter = TxFilter({'txid': Regex(r'\d\d')})
    assert tx_filter.match(tx)
    tx_filter = TxFilter({'txid': Include('664db4244663bcf32cada759279a840c')})
    assert tx_filter.match(tx)
    tx_filter = TxFilter({'size': Equal(381)})
    assert tx_filter.match(tx)
    tx_filter = TxFilter({'size': Different(381)})
    assert not tx_filter.match(tx)
    tx_filter = TxFilter({'input_values': Include(5071416)})
    assert tx_filter.match(tx)
    tx_filter = TxFilter({'input_values': Include(5071415)})
    assert not tx_filter.match(tx)
    tx_filter = TxFilter({'abs_fee': Greater(90000)})
    assert tx_filter.match(tx)
    tx_filter = TxFilter({'abs_fee': Lesser(90000)})
    assert tx_filter.match(tx)
