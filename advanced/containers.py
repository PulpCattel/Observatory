from collections import Counter
from datetime import datetime as dt


class Container:
    """
    Base object for containers
    """

    __slots__ = ()

    def __getitem__(self, item):
        return getattr(self, item)


class Tx(Container):
    """
    Object container for transactions as returned by Bitcoin Knots `getblock` method verbosity 3
    """

    __slots__ = ('txid', 'version', 'size', 'vsize', 'weight', 'locktime', 'inputs', 'n_in', 'outputs', 'n_out',
                 'n_eq', 'den', 'abs_fee', 'rel_fee', 'height', 'date')

    def __init__(self, transaction, date, subsidy, blockheight):
        self.txid = transaction['txid']
        self.version = transaction['version']
        self.size = transaction['size']
        self.vsize = transaction['vsize']
        self.weight = transaction['weight']
        self.locktime = transaction['locktime']
        self.inputs = [TxInput(tx_input, subsidy) for tx_input in transaction['vin']]
        self.n_in = len(transaction['vin'])
        self.outputs = [TxOutput(tx_output) for tx_output in transaction['vout']]
        self.n_out = len(self.outputs)
        input_values = (tx_input.value for tx_input in self.inputs)
        output_values = [tx_output.value for tx_output in self.outputs if tx_output.value > 0]
        count_values = Counter(output_values)
        try:
            n_eq = max(count_values.values())
        except ValueError:
            n_eq = 0
            den = 0
        else:
            if n_eq == 1:
                den = 0
            else:
                for key, value in count_values.items():
                    if value == n_eq:
                        den = key
                        break
        self.n_out = len(transaction['vout'])
        self.n_eq = n_eq
        self.den = den
        self.abs_fee = round(sum(input_values) - sum(output_values), 8)
        if self.abs_fee < 0:
            # It's coinbase transaction
            self.abs_fee = 0
        self.rel_fee = round(self.abs_fee * 1e8 / self.vsize, 2) if self.abs_fee else 0
        self.height = blockheight
        self.date = dt.utcfromtimestamp(date).strftime('%Y-%m-%d %H:%M')
        return

    @property
    def dict(self):
        return {attr: self[attr] if attr not in ('inputs', 'outputs') else
                [obj.dict for obj in self[attr]] for attr in self.__slots__}


class TxInput(Container):
    """
    Object container for transaction inputs as returned by Bitcoin Knots `getblock` method verbosity 3
    """

    __slots__ = ('txid', 'height', 'value', 'vout', 'addresses', 'type')

    def __init__(self, tx_input, subsidy):
        if 'txid' in tx_input:
            self.txid = tx_input['txid']
            self.height = tx_input['prevout']['height']
            self.value = tx_input['prevout']['value']
            self.vout = tx_input['vout']
            self.addresses = tx_input['prevout']['scriptPubKey']['addresses'] if 'addresses' in tx_input['prevout'][
                'scriptPubKey'] else []
            self.type = tx_input['prevout']['scriptPubKey']['type']
        else:
            self.txid = f'{tx_input["coinbase"]}'
            self.height = None
            self.value = subsidy / 1e8
            self.vout = None
            self.addresses = []
            self.type = 'coinbase'
        return

    @property
    def dict(self):
        return {attr: self[attr] for attr in self.__slots__}


class TxOutput(Container):
    """
    Object container for transaction outputs as returned by Bitcoin Knots `getblock` method verbosity 3
    """

    __slots__ = ('value', 'vout', 'addresses', 'type')

    def __init__(self, tx_output):
        self.value = tx_output['value']
        self.vout = tx_output['n']
        self.addresses = tx_output['scriptPubKey']['addresses'] if 'addresses' in tx_output[
            'scriptPubKey'] else []
        self.type = tx_output['scriptPubKey']['type']
        return

    @property
    def dict(self):
        return {attr: self[attr] for attr in self.__slots__}
