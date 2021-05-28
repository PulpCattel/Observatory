from collections import Counter
from datetime import datetime as dt
from typing import Dict, Any, Iterator, List, Optional, Iterable


class Container:
    """
    Base object for containers
    """

    __slots__ = ()

    def __getitem__(self, item: Any) -> Any:
        return getattr(self, item)


class TxInput(Container):
    """
    Object container for transaction inputs as returned by Bitcoin Knots `getblock` method verbosity 3
    """

    __slots__ = ('txid', 'height', 'value', 'vout', 'addresses', 'type')

    def __init__(self, tx_input: Dict[str, Any]) -> None:
        if 'txid' in tx_input:
            self.txid: str = tx_input['txid']
            self.height: Optional[int] = tx_input['prevout']['height']
            self.value: int = int(tx_input['prevout']['value'] * 1e8)
            self.vout: Optional[int] = tx_input['vout']
            self.addresses: List[str] = tx_input['prevout']['scriptPubKey']['addresses'] if 'addresses' in \
                                                                                            tx_input['prevout'][
                                                                                                'scriptPubKey'] else []
            self.type: str = tx_input['prevout']['scriptPubKey']['type']
        else:
            self.txid = f'{tx_input["coinbase"]}'
            self.height = None
            self.value = 0
            self.vout = None
            self.addresses = []
            self.type = 'coinbase'

    @property
    def dict(self) -> Dict[str, Any]:
        return {key: self[key] for key in self.__slots__}


class TxOutput(Container):
    """
    Object container for transaction outputs as returned by Bitcoin Knots `getblock` method verbosity 3
    """

    __slots__ = ('value', 'vout', 'addresses', 'type')

    def __init__(self, tx_output: Dict[str, Any]) -> None:
        self.value: int = int(tx_output['value'] * 1e8)
        self.vout: int = tx_output['n']
        self.addresses: List[str] = tx_output['scriptPubKey']['addresses'] if 'addresses' in tx_output[
            'scriptPubKey'] else []
        self.type: str = tx_output['scriptPubKey']['type']

    @property
    def dict(self) -> Dict[str, Any]:
        return {key: self[key] for key in self.__slots__}


class Tx(Container):
    """
    Object container for transactions as returned by Bitcoin Knots `getblock` method verbosity 3
    """

    __slots__ = ('txid', 'hash', 'version', 'size', 'vsize', 'weight', 'locktime', 'inputs', 'outputs',
                 'height', 'timestamp_date')

    def __init__(self, transaction: dict, date: int, block_height: int) -> None:
        self.txid: str = transaction['txid']
        self.hash: str = transaction['hash']
        self.version: int = transaction['version']
        self.size: int = transaction['size']
        self.vsize: int = transaction['vsize']
        self.weight: int = transaction['weight']
        self.locktime: int = transaction['locktime']
        self.inputs: list = [TxInput(tx_input) for tx_input in transaction['vin']]
        self.outputs: list = [TxOutput(tx_output) for tx_output in transaction['vout']]
        self.height: int = block_height
        self.timestamp_date: int = date

    @property
    def n_in(self) -> int:
        return len(self.inputs)

    @property
    def n_out(self) -> int:
        return len(self.outputs)

    @property
    def n_eq(self) -> int:
        """
        Return the frequency of the most common equally sized output.
        """
        return Counter(self.output_values).most_common(1)[0][1]

    @property
    def den(self) -> int:
        """
        Return the denomination, defined as the value in satoshi
        of the most common equally sized output.
        If no equally sized outputs, return 0
        """
        if self.n_eq > 1:
            return Counter(self.output_values).most_common(1)[0][0]
        return 0

    @property
    def abs_fee(self) -> int:
        if self.coinbase:
            return 0
        return self.inputs_sum - self.outputs_sum

    @property
    def rel_fee(self) -> float:
        if self.coinbase:
            return 0
        return round(self.abs_fee / self.vsize, 1)

    @property
    def date(self) -> str:
        return dt.utcfromtimestamp(self.timestamp_date).strftime('%Y-%m-%d %H:%M')

    @property
    def inputs_sum(self) -> int:
        return sum(self.input_values)

    @property
    def outputs_sum(self) -> int:
        return sum(self.output_values)

    @property
    def coinbase(self) -> bool:
        return 'coinbase' == self.inputs[0].type

    @property
    def addresses(self) -> Iterator[str]:
        """
        Yield each input and output address.
        """
        for side in [self.inputs, self.outputs]:
            for coin in side:
                for address in coin.addresses:
                    yield address

    @property
    def types(self) -> Iterator[str]:
        """
        Yield each coin type.
        """
        for side in [self.inputs, self.outputs]:
            for coin in side:
                yield coin.type

    @property
    def input_values(self) -> Iterator[int]:
        """
        Yield each input coin value, in satoshi.
        """
        for tx_input in self.inputs:
            yield tx_input.value

    @property
    def output_values(self) -> Iterator[int]:
        """
        Yield each output coin value, in satoshi.
        """
        for tx_output in self.outputs:
            yield tx_output.value

    def dict(self, keys: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        """
        Return dict representation of the transaction.
        Specify `keys` to select which keys to use in the dictionary.
        """
        return {key: self[key] if key not in ('inputs', 'outputs') else
                [obj.dict for obj in self[key]] for key in (keys if keys else self.__slots__)}
