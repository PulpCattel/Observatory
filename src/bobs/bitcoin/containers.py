"""
Module to handle Bitcoin objects
"""
from collections import Counter
from datetime import datetime as dt
from functools import cached_property
from itertools import chain
from typing import Dict, Any, List, Optional, Generator


class Container:
    """
    Base object for containers, meant to be used with Bitcoin Core REST API
    """

    __slots__ = ()

    def __getitem__(self, item):
        return getattr(self, item)


class TxInput(Container):
    """
    Transaction input composed by both the previous output and the signature.
    """

    __slots__ = ('txid', 'height', 'prevout', 'script_sig',
                 'sequence', 'txinwitness')

    def __init__(self, tx_input: Dict[str, Any]):
        if 'coinbase' not in tx_input:
            # Hash of the referenced transaction
            self.txid: Optional[str] = tx_input['txid']
            # Height of the block in which the outpoint was confirmed
            self.height: Optional[int] = tx_input['prevout']['height']
            # Previous TxOutput from which we are spending from
            self.prevout: Optional[TxOutput] = TxOutput({'value': tx_input['prevout']['value'],
                                                         'scriptPubKey': tx_input['prevout']['scriptPubKey'],
                                                         'n': tx_input['vout']})
            # Computational Script for confirming transaction authorization
            self.script_sig: Optional[str] = tx_input['scriptSig']['asm']
            # The sequence number, which suggests to miners which of two
            # conflicting transactions should be preferred, or 0xFFFFFFFF
            # to ignore this feature.
            self.sequence: int = tx_input['sequence']
            try:
                self.txinwitness: Optional[List[str]] = tx_input['txinwitness']
            except KeyError:
                self.txinwitness = None
        else:
            # It's a coinbase
            self.script_sig = tx_input['coinbase']
            self.sequence = tx_input['sequence']
            self.txid = None
            self.height = None
            self.prevout = None
            self.txinwitness = None

    @property
    def outpoint(self) -> Optional[str]:
        """
        A reference to a UTXO.
        """
        if self.prevout is None:
            return None
        return f'{self.txid}-{self.prevout.vout}'


class TxOutput(Container):
    """
    Transaction output
    """

    __slots__ = ('value', 'vout', 'script', 'address', 'type')

    def __init__(self, tx_output: Dict[str, Any]):
        # The value of the input, in sats
        self.value = int(tx_output['value'] * 1e8)
        # Index of the specific output in the transaction. The first output is 0
        self.vout: int = tx_output['n']
        if 'address' not in tx_output['scriptPubKey']:
            tx_output['scriptPubKey']['address'] = ''
        self.script: str = tx_output['scriptPubKey']['asm']
        self.address: str = tx_output['scriptPubKey']['address']
        self.type: str = tx_output['scriptPubKey']['type']


class Tx(Container):
    """
    Bitcoin transaction, includes previous output information
    """

    __slots__ = ('txid', 'hash', 'version', 'size', 'vsize', 'weight', 'locktime',
                 'inputs', 'outputs', 'height', 'timestamp_date', 'abs_fee', '__dict__')

    def __init__(self, transaction: Dict[str, Any], date: int, height: int):
        # The transaction id
        self.txid: str = transaction['txid']
        self.hash: str = transaction['hash']
        # The transaction version
        self.version: int = transaction['version']
        # The serialized transaction size
        self.size: int = transaction['size']
        # The virtual transaction size (differs from size for witness transactions)
        self.vsize: int = transaction['vsize']
        # The transaction's weight (between vsize*4-3 and vsize*4)
        self.weight: int = transaction['weight']
        # Block number before which this transaction is valid, or 0 for valid immediately.
        self.locktime: int = transaction['locktime']
        self.inputs = list(map(TxInput, transaction['vin']))
        self.outputs = list(map(TxOutput, transaction['vout']))
        self.height = height
        # The block time expressed in UNIX epoch time
        self.timestamp_date = date
        try:
            self.abs_fee = int(transaction['fee'] * 1e8)
        except KeyError:
            if self.is_coinbase:
                self.abs_fee = 0
            else:
                self.abs_fee = self.inputs_sum - self.outputs_sum

    @cached_property
    def is_coinbase(self) -> bool:
        """
        Return whether the transaction is a coinbase or not.
        """
        return self.inputs[0].prevout is None

    @cached_property
    def n_in(self) -> int:
        """
        Return number of inputs
        """
        return len(self.inputs)

    @cached_property
    def n_out(self) -> int:
        """
        Return number of outputs
        """
        return len(self.outputs)

    @cached_property
    def in_counter(self) -> Counter:
        """
        Return Counter with value:frequency pairs for input values
        """
        return Counter(self.input_values)

    @cached_property
    def out_counter(self) -> Counter:
        """
        Return Counter with value:frequency pairs for output values
        """
        return Counter(self.output_values)

    @cached_property
    def n_eq(self) -> int:
        """
        Return the frequency of the most common equally sized output.
        """
        return self.out_counter.most_common(1)[0][1]

    @cached_property
    def den(self) -> int:
        """
        Return the denomination, defined as the value in satoshi
        of the most common equally sized output.
        If no equally sized outputs, return 0
        """
        return self.out_counter.most_common(1)[0][0] if self.n_eq > 1 else 0

    @cached_property
    def rel_fee(self) -> float:
        """
        Return relative fee in sat/vb
        """
        return 0 if self.is_coinbase else round(self.abs_fee / self.vsize, 1)

    @cached_property
    def date(self) -> str:
        """
        Return transaction time in datetime
        """
        return dt.utcfromtimestamp(self.timestamp_date).strftime('%Y-%m-%d %H:%M')

    @cached_property
    def inputs_sum(self) -> int:
        """
        Return sum of all inputs, in sats
        """
        return sum(self.input_values)

    @cached_property
    def outputs_sum(self) -> int:
        """
        Return sum of all outputs, in sats
        """
        return sum(self.output_values)

    @property
    def addresses(self) -> Generator[str, None, None]:
        """
        Yield each address.
        """
        for address in chain(self.in_addrs, self.out_addrs):
            yield address

    @property
    def in_addrs(self) -> Generator[str, None, None]:
        """
        Yield each input address.
        """
        if self.is_coinbase:
            return
        for tx_input in self.inputs:
            yield tx_input.prevout.address

    @property
    def out_addrs(self) -> Generator[str, None, None]:
        """
        Yield each output address.
        """
        for output in self.outputs:
            yield output.address

    @property
    def types(self) -> Generator[str, None, None]:
        """
        Yield each input/output script type.
        """
        for t in chain(self.in_types, self.out_types):
            yield t

    @property
    def in_types(self) -> Generator[str, None, None]:
        """
        Yield each input script type
        """
        if self.is_coinbase:
            return
        for tx_input in self.inputs:
            yield tx_input.prevout.type

    @property
    def out_types(self) -> Generator[str, None, None]:
        """
        Yield each output script type
        """
        for output in self.outputs:
            yield output.type

    @property
    def input_values(self) -> Generator[int, None, None]:
        """
        Yield each input coin value, in satoshi.
        """
        if self.is_coinbase:
            return
        for tx_input in self.inputs:
            yield tx_input.prevout.value

    @property
    def output_values(self) -> Generator[int, None, None]:
        """
        Yield each output coin value, in satoshi.
        """
        for output in self.outputs:
            yield output.value
