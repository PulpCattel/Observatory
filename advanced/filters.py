class Filter:
    """
    Base class for filters. Valid criteria include any object attribute
    """

    def __init__(self, **criteria):
        self.criteria = criteria

    def match(self, obj):
        for key in self.criteria:
            if not getattr(self, f'match_{key}')(obj):
                return False
        return True

    def __getattr__(self, method):

        def match_attr(obj):
            attr = method.split('match_')[1]
            try:
                value = obj[attr]
            except (ValueError, TypeError):
                value = getattr(obj, attr)
            if not self.criteria[attr][0] <= value <= self.criteria[attr][1]:
                return False
            return True

        return match_attr

    def match_callables(self, obj):
        for c in self.criteria['callables']:
            if not c(obj):
                return False
        return True


class TxFilter(Filter):
    """
    Base class for transaction filters.
    Transaction filters accept any number of criteria.
    Valid criteria include any Tx object attribute plus few other.
    You can also pass arbitrary callables as long as they take a Tx object as argument and return True or False
    """

    def match_txid(self, tx):
        if self.criteria['txid'] not in tx.txid:
            return False
        return True

    def match_address(self, tx):
        tx_addresses = [address for side in [tx.inputs, tx.outputs] for tx in side for address in tx.addresses]
        for c_addr in self.criteria['address']:
            if not any(c_addr in address for address in tx_addresses):
                return False
        return True

    def match_in_type(self, tx):
        for tx_input in tx.inputs:
            if 'coinbase' in tx_input.type:
                if self.criteria['in_type'] != 'coinbase':
                    return False
                return True
            if tx_input.type != self.criteria['in_type']:
                return False
        return True

    def match_out_type(self, tx):
        for tx_output in tx.outputs:
            if tx_output.type != self.criteria['out_type']:
                return False
        return True


class CjTxFilter(TxFilter):
    """
    Custom made filter for scanning CoinJoin like transactions.
    Criteria:
    Number equal outputs >= 3
    Number inputs >= 3
    At least 10k satoshis as denomination
    """

    def __init__(self, **criteria):
        super().__init__(n_eq=(3, 10000), n_in=(3, 10000), den=(0.0001, 21 * 1e6), **criteria)
        return


class WasabiTxFilter(CjTxFilter):
    """
    Custom made filter for scanning Wasabi like CoinJoin transactions.
    Criteria:
    N equal sized outputs where N >=5
    Number inputs >= 5
    Inputs and outputs type 'witness_v0_keyhash' (bech32)
    0.089 <= denomination <= 0.11
    """

    def __init__(self, **criteria):
        super().__init__(**criteria)
        self.criteria['n_eq'] = (5, 10000)
        self.criteria['n_in'] = (5, 10000)
        self.criteria['den'] = (0.089, 0.11)
        self.criteria['in_type'] = 'witness_v0_keyhash'
        self.criteria['out_type'] = 'witness_v0_keyhash'
        return


class JoinmarketTxFilter(CjTxFilter):
    """
    Custom made filter for scanning JoinMarket like CoinJoin transactions.
    Criteria:
    N equal sized outputs where N >=3
    At least N inputs
    Either N or N-1 additional outputs of size different from the N equal outputs.
    At least 10k satoshis as denomination
    """

    def __init__(self, **criteria):
        super().__init__(**criteria)
        if 'callables' in self.criteria:
            if match_joinmarket not in self.criteria['callables']:
                self.criteria['callables'].append(match_joinmarket)
        else:
            self.criteria['callables'] = [match_joinmarket]
        return


class TxidTxFilter(TxFilter):
    """
    Custom made filter for scanning a specific txid
    """

    def __init__(self, txid, **criteria):
        super().__init__(**criteria)
        self.criteria['txid'] = txid
        return


class AddressTxFilter(TxFilter):
    """
    Custom made filter for scanning specific addresses
    """

    def __init__(self, *addresses, **criteria):
        super().__init__(**criteria)
        self.criteria['address'] = addresses
        return


class CoinbaseTxFilter(TxFilter):
    """
    Custom made filter for scanning coinbase transanctions
    """

    def __init__(self, **criteria):
        super().__init__(**criteria)
        self.criteria['in_type'] = 'coinbase'
        return


def match_joinmarket(tx):
    """
    Function for filter callable
    """
    if not (tx.n_out == tx.n_eq * 2 or tx.n_out == tx.n_eq * 2 - 1):
        return False
    if not tx.n_in >= tx.n_eq:
        return False
    return True
