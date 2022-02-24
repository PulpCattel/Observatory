"""
Modules for filters and criteria
"""
from abc import ABC, abstractmethod
from enum import Enum
from re import compile as re_compile
from typing import Callable, Optional, Mapping, AnyStr, Dict, Type, Tuple, cast, Pattern

from bobs.types import Any_
from marshmallow import fields, ValidationError


class Criterion(ABC):
    """
    A Criterion represents characterizing marks or traits
    that a candidate should have in order to match the Criterion.
    Can also be thought of as a condition.
    """

    __slots__ = ()

    def __eq__(self, other: Any_) -> bool:
        """
        Most useful for testing purposes.
        """
        if not isinstance(other, self.__class__) or self.__slots__ != other.__slots__:
            return False
        return all(getattr(self, attr) == getattr(other, attr) for attr in cast(Tuple[str], self.__slots__))

    @abstractmethod
    def __call__(self, candidate: Any_) -> bool:
        """
        Call this Criterion on a candidate, if the candidate matches the Criterion, return True, else False.
        """


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

    __slots__ = ('_value', '_inclusive')

    def __init__(self, value: Any_, inclusive: bool = True) -> None:
        self._value = value
        self._inclusive = inclusive

    def __call__(self, candidate: Any_) -> bool:
        if self._inclusive:
            return candidate >= self._value
        return candidate > self._value


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

    __slots__ = ('_value', '_inclusive')

    def __init__(self, value: Any_, inclusive: bool = True) -> None:
        self._value = value
        self._inclusive = inclusive

    def __call__(self, candidate: Any_) -> bool:
        if self._inclusive:
            return candidate <= self._value
        return candidate < self._value


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

    __slots__ = ('_min', '_max', '_inclusive')

    def __init__(self, min_: Any_, max_: Any_, inclusive: bool = True) -> None:
        self._min = min_
        self._max = max_
        self._inclusive = inclusive

    def __call__(self, candidate: Any_) -> bool:
        if self._inclusive:
            return self._min <= candidate <= self._max
        return self._min < candidate < self._max


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

    __slots__ = ('_value',)

    def __init__(self, value: Any_) -> None:
        self._value = value

    def __call__(self, candidate: Any_) -> bool:
        return candidate == self._value


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

    __slots__ = ('_value',)

    def __init__(self, value: Any_) -> None:
        self._value = value

    def __call__(self, candidate: Any_) -> bool:
        return candidate != self._value


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

    __slots__ = ('_value',)

    def __init__(self, value: Any_) -> None:
        self._value = value

    def __call__(self, candidate: Any_) -> bool:
        return self._value in candidate


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

    __slots__ = ('_value',)

    def __init__(self, value: Any_) -> None:
        self._value = value

    def __call__(self, candidate: Any_) -> bool:
        return candidate in self._value


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

    __slots__ = ('_value',)

    def __init__(self, value: Callable[[Any_], bool]) -> None:
        self._value = value

    def __call__(self, candidate: Any_) -> bool:
        return self._value(candidate)


class Regex(Criterion):
    """
    A criterion that represents a regex search.

    >>> regex = Regex(r'12')
    >>> regex('123')
    True
    >>> regex('abc')
    False
    """

    __slots__ = ('_value',)

    def __init__(self, value: AnyStr) -> None:
        self._value: Pattern[AnyStr] = re_compile(value)  # type: ignore[arg-type] # it complaints about the string type
        # TODO: fix

    def __call__(self, candidate: AnyStr) -> bool:
        return self._value.search(candidate) is not None  # type: ignore[arg-type] # it complaints about the string type
        # TODO: fix


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
        Only CriterionTypes are accepted.
        """
        whitelisted_names: Dict[str, Type[Criterion]] = {member.value.__name__: member.value for member in
                                                         CriterionType}
        code = compile(string, "<string>", "eval")
        for name in code.co_names:
            if name in whitelisted_names:
                continue
            raise ValidationError(f"Use of `{name}` not allowed")
        return eval(code, {"__builtins__": {}}, whitelisted_names)  # pylint: disable=eval-used

    def _deserialize(
            self,
            value: str,
            attr: Optional[str],
            data: Optional[Mapping[str, Any_]],
            **kwargs: Any_,
    ) -> Criterion:
        """
        Transform a string representation of a Criterion into a Criterion instance
        using a restricted version of eval.
        `Satisfy` Criterion is not restricted.
        """
        value = value.strip()
        if value.startswith("Satisfy"):
            return eval(value)  # pylint: disable=eval-used
        return self._restricted_eval(value)
