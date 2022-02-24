"""
Wrapper objects returned by Targets, useful to process lazily and on-the-fly all the interesting information
about some raw data.
"""

from collections import Counter
from datetime import datetime as dt
from functools import cached_property
from itertools import starmap, chain
from operator import attrgetter, itemgetter
from statistics import median, mean
from typing import Mapping, Iterator, Counter as Counter_t, Union

from bobs.obs.criteria import Criterion
from bobs.types import RawData, Any_
from orjson import dumps


class Candidate:
    """
    Base class for candidates, defined as the things that are matched against some criteria. A candidate behaves as a
    transparent wrapper around some Dict-like object, and it can spit out all the precise information about it.
    """

    # We use __dict__ to cache properties
    __slots__ = ('raw_data', '__dict__')

    def __init__(self, raw_data: RawData) -> None:
        """
        Initialized with raw data.
        """
        self.raw_data = raw_data

    def __getattr__(self, item: str) -> Any_:
        return self.raw_data[item]

    def __getitem__(self, item: str) -> Any_:
        return self.raw_data[item]

    def __contains__(self, item: str) -> bool:
        return item in self.raw_data

    def __str__(self) -> str:
        return dumps(self.raw_data).decode('UTF-8')

    def __call__(self, filter_: Mapping[str, Criterion]) -> bool:
        """
        Return True if the candidate match all criterion in the filter.
        """
        return all(starmap(self.match_criterion, filter_.items()))

    def match_criterion(self, id_: str, criterion: Criterion) -> bool:
        """
        Return True if the given `criterion` satisfies filter chosen value.
        The id_ is the identifier of an attribute of the candidate to be used as value. If no such attribute,
        use the entire candidate object.
        """
        try:
            return criterion(getattr(self, id_))
        except (KeyError, AttributeError):
            return criterion(self)


class Transaction(Candidate):
    """
    Base candidate for transactions.
    """

    @property
    def inputs(self) -> Iterator[RawData]:
        return iter(self.raw_data['vin'])

    @property
    def outputs(self) -> Iterator[RawData]:
        return iter(self.raw_data['vout'])

    @cached_property
    def is_coinbase(self) -> bool:
        return 'coinbase' in self.raw_data['vin'][0]

    @property
    def out_values(self) -> Iterator[float]:
        """
        Yield each output coin value, in bitcoin.
        """
        return map(itemgetter('value'), self.raw_data['vout'])

    @cached_property
    def total_out(self) -> float:
        """
        Return sum of all outputs, in bitcoin
        """
        return round(sum(self.out_values), 8)

    @cached_property
    def n_in(self) -> int:
        """
        Return number of inputs
        """
        return len(self.raw_data['vin'])

    @cached_property
    def n_out(self) -> int:
        """
        Return number of outputs
        """
        return len(self.raw_data['vout'])

    @cached_property
    def out_counter(self) -> Counter_t[float]:
        """
        Return Counter with value:frequency pairs for output values
        """
        return Counter(self.out_values)

    @cached_property
    def n_eq(self) -> int:
        """
        Return the frequency of the **most common** equally sized output.
        """
        return self.out_counter.most_common(1)[0][1]

    @cached_property
    def den(self) -> float:
        """
        Return the denomination, defined as the value
        of the most common equally sized output.
        If no equally sized outputs, return 0
        """
        return self.out_counter.most_common(1)[0][0] if self.n_eq > 1 else 0

    @cached_property
    def date(self) -> str:
        """
        Return transaction time in datetime.
        """
        return dt.utcfromtimestamp(self.raw_data['timestamp_date']).strftime('%Y-%m-%d %H:%M')

    @property
    def out_addrs(self) -> Iterator[str]:
        """
        Yield each output address.
        """
        for tx_output in self.raw_data['vout']:
            yield tx_output['scriptPubKey'].get('address', '')

    @property
    def out_types(self) -> Iterator[str]:
        """
        Yield each output script type
        """
        if self.is_coinbase:
            return
        for tx_output in self.raw_data['vout']:
            yield tx_output['scriptPubKey']['type']


class TransactionV3(Transaction):
    """
    Transaction candidate with extra prevout information as returned by getblock verbosity 3
    """

    @property
    def in_values(self) -> Iterator[float]:
        """
        Yield each input coin value, in bitcoin.
        """
        if self.is_coinbase:
            return
        for tx_input in self.raw_data['vin']:
            yield tx_input['prevout']['value']

    @cached_property
    def total_in(self) -> float:
        """
        Return sum of all inputs, in bitcoin
        """
        return round(sum(self.in_values), 8)

    @cached_property
    def abs_fee(self) -> float:
        """
        Return absolute fee, in bitcoin.
        """
        try:
            return self.fee  # type: ignore[no-any-return] # It's from raw data, we assume it's indeed a float
        except KeyError:
            if self.is_coinbase:
                return 0.0
            return round(self.total_in - self.total_out, 8)

    @cached_property
    def rel_fee(self) -> float:
        """
        Return relative fee in sat/vb
        """
        if self.is_coinbase:
            return 0.0
        rel_fee: float = round(self.abs_fee * 1e8 / self.vsize, 1)
        return rel_fee

    @cached_property
    def in_counter(self) -> Counter_t[float]:
        """
        Return Counter with value:frequency pairs for input values
        """
        return Counter(self.in_values)

    @property
    def in_addrs(self) -> Iterator[str]:
        """
        Yield each input address.
        """
        if self.is_coinbase:
            return
        for tx_input in self.raw_data['vin']:
            yield tx_input['prevout']['scriptPubKey'].get('address', '')

    @property
    def addresses(self) -> Iterator[str]:
        """
        Yield each address.
        """
        return chain(self.in_addrs, self.out_addrs)

    @property
    def in_types(self) -> Iterator[str]:
        """
        Yield each input script type
        """
        if self.is_coinbase:
            return
        for tx_input in self.raw_data['vin']:
            yield tx_input['prevout']['scriptPubKey']['type']

    @property
    def types(self) -> Iterator[str]:
        """
        Yield each input/output script type.
        """
        return chain(self.in_types, self.out_types)


class Block(Candidate):
    """
    Base candidate for blocks.
    """

    @property
    def txs(self) -> Iterator[str]:
        """
        Base block only includes TXIDs.
        """
        return iter(self.raw_data['tx'])

    @cached_property
    def date(self) -> str:
        return dt.utcfromtimestamp(self.raw_data['time']).strftime('%Y-%m-%d %H:%M')


class BlockV3(Block):

    @property
    def txs(self) -> Iterator[TransactionV3]:  # type: ignore[override] # Intentional
        return map(TransactionV3, self.raw_data['tx'])

    @property
    def n_in(self) -> int:
        return sum(map(attrgetter('n_in'), self.txs))

    @property
    def n_out(self) -> int:
        return sum(map(attrgetter('n_out'), self.txs))

    @property
    def abs_fees(self) -> Iterator[float]:
        return map(attrgetter('abs_fee'), self.txs)

    @property
    def rel_fees(self) -> Iterator[float]:
        return map(attrgetter('rel_fee'), self.txs)

    @cached_property
    def total_fee(self) -> float:
        return sum(self.abs_fees)

    @cached_property
    def median_fee(self) -> Union[int, float]:
        return median(self.abs_fees)

    @cached_property
    def mean_fee(self) -> Union[int, float]:
        return mean(self.abs_fees)

    @cached_property
    def median_rel_fee(self) -> float:
        return median(self.rel_fees)

    @cached_property
    def mean_rel_fee(self) -> float:
        return mean(self.rel_fees)

    @cached_property
    def total_in(self) -> float:
        """
        Total value of inputs, in bitcoin
        """
        return sum(map(attrgetter('total_in'), self.txs))

    @cached_property
    def total_out(self) -> float:
        """
        Total value of outputs, in bitcoin
        """
        return sum(map(attrgetter('total_out'), self.txs))


class MempoolTx(Candidate):
    """
    Base candidate for mempool transaction as returned by get_mempool.
    This contains mostly fee related infos.
    """


class MempoolTxV2(MempoolTx, Transaction):
    pass


class MempoolTxV3(MempoolTxV2, TransactionV3):
    pass
