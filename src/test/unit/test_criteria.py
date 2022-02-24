"""
Criteria objects unit tests
"""
from re import compile as re_compile
from typing import Union, List, Set

import pytest
from bobs.obs.criteria import CriterionField, Greater, Regex, Include, Equal, Different, Lesser, Between, \
    Appear, Satisfy
from bobs.types import DrawObject
from hypothesis import given, strategies as st
from marshmallow import ValidationError


# pylint: disable=protected-access


@given(st.integers(), st.integers())
def test_greater(value: int, candidate: int) -> None:
    greater = Greater(value)
    if candidate == value:
        assert greater(candidate) is True
    if candidate > value:
        assert greater(candidate) is True
    if candidate < value:
        assert greater(candidate) is False
    greater = Greater(value, inclusive=False)
    if candidate == value:
        assert greater(candidate) is False
    if candidate > value:
        assert greater(candidate) is True
    if candidate < value:
        assert greater(candidate) is False


@given(st.integers(), st.integers())
def test_lesser(value: int, candidate: int) -> None:
    lesser = Lesser(value)
    if candidate == value:
        assert lesser(candidate) is True
    if candidate < value:
        assert lesser(candidate) is True
    if candidate > value:
        assert lesser(candidate) is False
    lesser = Lesser(value, inclusive=False)
    if candidate == value:
        assert lesser(candidate) is False
    if candidate < value:
        assert lesser(candidate) is True
    if candidate > value:
        assert lesser(candidate) is False


@given(st.integers(), st.integers(), st.integers())
def test_between(min_: int, max_: int, candidate: int) -> None:
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
def test_equal(value: str, candidate: str) -> None:
    equal = Equal(value)
    if candidate == value:
        assert equal(candidate) is True
    else:
        assert equal(candidate) is False


@given(st.text(), st.text())
def test_different(value: str, candidate: str) -> None:
    different = Different(value)
    if candidate != value:
        assert different(candidate) is True
    else:
        assert different(candidate) is False


@given(st.data())
def test_include(data: DrawObject) -> None:
    value: Union[int, str] = data.draw(st.one_of(st.integers(), st.text()))
    include = Include(value)
    candidate: Union[List[int], Set[int], str]
    if isinstance(value, int):
        candidate = data.draw(st.one_of(st.lists(st.integers()), st.sets(st.integers())))
    else:
        candidate = data.draw(st.text())
    if value in candidate:
        assert include(candidate) is True
    else:
        assert include(candidate) is False


@given(st.one_of(st.text(), st.lists(st.text())), st.text())
def test_appear(value: Union[str, List[str]], candidate: str) -> None:
    appear = Appear(value)
    if candidate in value:
        assert appear(candidate) is True
    else:
        assert appear(candidate) is False


@given(st.integers())
def test_satisfy(candidate: int) -> None:
    def example_callable(num: int) -> bool:
        return num + 1 == 1

    satisfy = Satisfy(example_callable)
    if example_callable(candidate):
        assert satisfy(candidate) is True
    else:
        assert satisfy(candidate) is False


@given(st.text())
def test_regex(candidate: str) -> None:
    value = r'\d'
    pattern = re_compile(value)
    regex = Regex(value)
    if pattern.search(candidate) is not None:
        assert regex(candidate) is True
    else:
        assert regex(candidate) is False


def test_deserialize() -> None:
    str_criterion = "Greater(5)"
    assert CriterionField()._deserialize(str_criterion, '', {}) == Greater(5)
    invalid_criterion = 'Invalid'
    with pytest.raises(ValidationError):
        CriterionField()._deserialize(invalid_criterion, '', {})


def test_restricted_eval() -> None:
    forbidden_string = "len([1, 2, 3])"
    with pytest.raises(ValidationError):
        CriterionField._restricted_eval(forbidden_string)
    forbidden_string = "''.__class__"
    with pytest.raises(ValidationError):
        CriterionField._restricted_eval(forbidden_string)
    accepted_string = "Greater(5)"
    assert Greater(5) == CriterionField._restricted_eval(accepted_string)
