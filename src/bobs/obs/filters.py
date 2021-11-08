"""
Modules for filters and criteria
"""
from enum import Enum
from itertools import starmap
from re import compile as re_compile
from typing import Any, Callable, Optional, Mapping, Dict

from bobs.bitcoin.containers import Tx
from marshmallow import fields, ValidationError


class Criterion:
    """
    A Criterion represents characterizing marks or traits
    that a candidate should have in order to match the Criterion.
    Can also be thought of as a condition.
    """

    __slots__ = ()

    def __eq__(self, other):
        if not isinstance(other, self.__class__) or self.__slots__ != other.__slots__:
            return False
        return all(getattr(self, attr) == getattr(other, attr) for attr in self.__slots__)

    def __call__(self, candidate: Any) -> bool:
        """
        Call this Criterion on a candidate, if the candidate matches the Criterion, return True, else False.
        """
        raise NotImplementedError("Override this method in subclasses.")


class Greater(Criterion):
    """
    A Criterion that represents:

    If inclusive: `candidate` >= `Criterion value`

    If not inclusive: `candidate` > `Criterion value`

    Inclusive is the default.

    >>> greater = Greater(5)
    >>> greater(5)
    True
    >>> greater(7)
    True
    >>> greater(4)
    False
    """

    __slots__ = ('value', 'inclusive')

    def __init__(self, value: Any, inclusive: bool = True):
        self.value = value
        self.inclusive = inclusive

    def __call__(self, candidate: Any) -> bool:
        if self.inclusive:
            return candidate >= self.value
        return candidate > self.value


class Lesser(Criterion):
    """
    A Criterion that represents:

    If inclusive: `candidate` <= `Criterion value`

    If not inclusive: `candidate` < `Criterion value`

    Inclusive is the default.

    >>> lesser = Lesser(5)
    >>> lesser(5)
    True
    >>> lesser(7)
    False
    >>> lesser(4)
    True
    """

    __slots__ = ('value', 'inclusive')

    def __init__(self, value: Any, inclusive: bool = True):
        self.value = value
        self.inclusive = inclusive

    def __call__(self, candidate: Any) -> bool:
        if self.inclusive:
            return candidate <= self.value
        return candidate < self.value


class Between(Criterion):
    """
    A Criterion that represents:

    If inclusive: `Criterion min` <= `candidate` <= `Criterion max`

    If not inclusive: `Criterion min` < `candidate` < `Criterion max`

    Inclusive is the default.

    >>> between = Between(5, 10)
    >>> between(5)
    True
    >>> between(7)
    True
    >>> between(4)
    False
    """

    __slots__ = ('greater', 'lesser')

    def __init__(self, min_: Any, max_: Any, inclusive: bool = True):
        self.greater = Greater(min_, inclusive)
        self.lesser = Lesser(max_, inclusive)

    def __call__(self, candidate: Any) -> bool:
        return self.greater(candidate) and self.lesser(candidate)


class Equal(Criterion):
    """
    A Criterion that represents:

    `Candidate` == `Criterion value``

    >>> equal = Equal("Hello")
    >>> equal("Hello")
    True
    >>> equal("Hello world")
    False
    """

    __slots__ = ('value',)

    def __init__(self, value: Any):
        self.value = value

    def __call__(self, candidate: Any) -> bool:
        return candidate == self.value


class Different(Criterion):
    """
    A Criterion that represents:

    `Candidate` != `Criterion value``

    >>> different = Different("Hello")
    >>> different("Hello world")
    True
    >>> different("Hello")
    False
    """

    __slots__ = ('equal',)

    def __init__(self, value: Any):
        self.equal = Equal(value)

    def __call__(self, candidate: Any) -> bool:
        return not self.equal(candidate)


class Include(Criterion):
    """
    A Criterion that represents:

    `Candidate`.__contains__(`Criterion value`)

    >>> include = Include("Hello")
    >>> include("Hello world")
    True
    >>> include("hello world")
    False
    """

    __slots__ = ('value',)

    def __init__(self, value: Any):
        self.value = value

    def __call__(self, candidate: Any) -> bool:
        return self.value in candidate


class Appear(Criterion):
    """
    A Criterion that represents:

    `Criterion value`.__contains__(`Candidate`)

    >>> appear = Appear("Hello world")
    >>> appear("Hello")
    True
    >>> appear("hello")
    False
    """

    __slots__ = ('value',)

    def __init__(self, value: Any):
        self.value = value

    def __call__(self, candidate: Any) -> bool:
        return candidate in self.value


class Satisfy(Criterion):
    """
    A Criterion that represents:

    `Criterion value`(candidate) is True.

    >>> satisfy = Satisfy(lambda x: x + 1 == 1)
    >>> satisfy(0)
    True
    >>> satisfy(1)
    False
    """

    __slots__ = ('value',)

    def __init__(self, value: Callable):
        self.value = value

    def __call__(self, candidate: Any) -> bool:
        return self.value(candidate)


class Regex(Criterion):
    """
    A criterion that represents a regex search.

    >>> regex = Regex(r'\d\d')
    >>> regex('123')
    True
    >>> regex('abc')
    False
    """

    __slots__ = ('value',)

    def __init__(self, value: str):
        self.value = re_compile(value)

    def __call__(self, candidate) -> bool:
        return bool(self.value.search(candidate))


class CriterionType(Enum):
    GREATER = Greater
    LESSER = Lesser
    BETWEEN = Between
    EQUAL = Equal
    DIFFERENT = Different
    INCLUDE = Include
    APPEAR = Appear
    SATISFY = Satisfy
    REGEX = Regex


class CriterionField(fields.Field):
    """
    Field that deserializes to a Criterion.
    """

    @staticmethod
    def _restricted_eval(string: str) -> Criterion:
        """
        Only CriterionType is accepted
        """
        whitelisted_names = {member.value.__name__: member.value for member in CriterionType}
        code = compile(string, "<string>", "eval")
        for name in code.co_names:
            if name in whitelisted_names:
                continue
            raise ValidationError(f"Use of `{name}` not allowed")
        return eval(code, {"__builtins__": {}}, whitelisted_names)

    def _deserialize(
            self,
            value: str,
            attr: Optional[str],
            data: Optional[Mapping[str, Any]],
            **kwargs,
    ) -> Criterion:
        """
        Transform a string representation of a Criterion into a Criterion instance
        using a restricted version of eval.
        `Satisfy` Criterion is not restricted.
        """
        value = value.strip()
        if value.startswith("Satisfy"):
            return eval(value)
        return self._restricted_eval(value)


class TxFilter:
    """
    Collection of Criterion, with method to conveniently match those to a candidate.
    """

    __slots__ = ('title', 'criteria', '_current_candidate')

    def __init__(self, criteria: Dict[str, Any], title: str = 'Tx filter'):
        self.title = title
        self.criteria = criteria
        self._current_candidate: Optional[Tx] = None

    def __str__(self):
        return f'{self.title} filter'

    def match(self, candidate: Tx, match_all: bool = True) -> bool:
        """
        Return True if the candidate match all/any criterion in the filter depending
        on `match_all`.
        """
        self._current_candidate = candidate
        matches = starmap(self._match_criterion, self.criteria.items())
        return all(matches) if match_all else any(matches)

    def _match_criterion(self, id_: str, criterion: Criterion) -> bool:
        """
        Return True if the given `criterion` satisfies filter candidate.
        """
        try:
            return criterion(self._current_candidate[id_])
        except (KeyError, AttributeError):
            return criterion(self._current_candidate)
