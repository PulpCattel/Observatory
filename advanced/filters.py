try:
    from containers import Tx
except ModuleNotFoundError:
    from advanced.containers import Tx
from typing import Dict, Any


class Filter:
    """
    Base class for filters.
    Add match_something() methods to subclasses to make them callable by the match() method here.
    Built-in match_callables() to match arbitrary callables.
    """

    def __init__(self, **criteria):
        self.criteria: Dict[str, Any] = criteria

    def match(self, obj: Any, *args, **kwargs) -> bool:
        """
        Call match_criteria(candidate, *args, **kwargs) for each criteria.
        Pass obj.criteria if present, otherwise obj, as candidate.
        Return False if at least one of the calls returns False.
        Return True if no single call returns False or the filter holds no criteria.
        """

        def get_candidate(key: str) -> Any:
            try:
                candidate: Any = getattr(obj, key)
            except AttributeError:
                candidate = obj
            return candidate

        return all(getattr(self, f'match_{key}')(get_candidate(key), *args, **kwargs) for key in self.criteria)

    def match_callables(self, obj: object, *args, **kwargs) -> bool:
        return all(c(obj, *args, **kwargs) for c in self.criteria['callables'])


class TxFilter(Filter):
    """
    Base class for transaction filters.
    Meant to be use with Tx containers.
    """

    def __init__(self, **criteria):
        super().__init__(**criteria)

    def match_txid(self, txid: str) -> bool:
        """
        Check TXID
        """
        return self.criteria['txid'] in txid

    def match_hash(self, tx_hash: str) -> bool:
        """
        Check hash
        """
        return self.criteria['hash'] in tx_hash

    def match_version(self, version: int) -> bool:
        """
        Check version
        """
        return self.criteria['version'][0] <= version <= self.criteria['version'][1]

    def match_size(self, size: int) -> bool:
        """
        Check size
        """
        return self.criteria['size'][0] <= size <= self.criteria['size'][1]

    def match_vsize(self, vsize: int) -> bool:
        """
        Check virtual size
        """
        return self.criteria['vsize'][0] <= vsize <= self.criteria['vsize'][1]

    def match_weight(self, weight: int) -> bool:
        """
        Check weight
        """
        return self.criteria['weight'][0] <= weight <= self.criteria['weight'][1]

    def match_locktime(self, locktime: int) -> bool:
        """
        Check locktime
        """
        return self.criteria['locktime'][0] <= locktime <= self.criteria['locktime'][1]

    def match_n_in(self, n_in: int) -> bool:
        """
        Check number of inputs
        """
        return self.criteria['n_in'][0] <= n_in <= self.criteria['n_in'][1]

    def match_n_out(self, n_out: int) -> bool:
        """
        Check number of outputs
        """
        return self.criteria['n_out'][0] <= n_out <= self.criteria['n_out'][1]

    def match_n_eq(self, n_eq: int) -> bool:
        """
        Check number of equally sized outputs
        """
        return self.criteria['n_eq'][0] <= n_eq <= self.criteria['n_eq'][1]

    def match_den(self, den: int) -> bool:
        """
        Check denomination
        """
        return self.criteria['den'][0] <= den <= self.criteria['den'][1]

    def match_abs_fee(self, abs_fee: int) -> bool:
        """
        Check absolute fee
        """
        return self.criteria['abs_fee'][0] <= abs_fee <= self.criteria['abs_fee'][1]

    def match_rel_fee(self, rel_fee: float) -> bool:
        """
        Check relative fee
        """
        return self.criteria['rel_fee'][0] <= rel_fee <= self.criteria['rel_fee'][1]

    def match_height(self, height: int) -> bool:
        """
        Check block height
        """
        return self.criteria['height'][0] <= height <= self.criteria['height'][1]

    def match_date(self, date: str):
        """
        Check date
        """
        return self.criteria['date'][0] <= date <= self.criteria['date'][1]

    def match_address(self, tx: Tx) -> bool:
        """
        Check address appears in Tx
        """
        return any(self.criteria['address'] in address for address in tx.addresses)

    def match_in_type(self, tx: Tx) -> bool:
        """
        Check Tx input types all match
        """
        return all(tx_input.type == self.criteria['in_type'] for tx_input in tx.inputs)

    def match_out_type(self, tx: Tx) -> bool:
        """
        Check Tx output types all match
        """
        return all(tx_output.type == self.criteria['out_type'] for tx_output in tx.outputs)

    def match_coinbase(self, is_coinbase: bool) -> bool:
        return is_coinbase == self.criteria['coinbase']


# TODO
# class BlockFilter(Filter):
#     """
#     Base class for block filters.
#     """
#
#     def __init__(self, **criteria):
#         super().__init__(**criteria)


class TxidFilter(TxFilter):
    """
    Custom made TxFilter to scan for a specific txid.
    """

    def __init__(self, txid: str, **criteria):
        super().__init__(txid=txid, **criteria)


class AddressFilter(TxFilter):
    """
    Custom made TxFilter to scan for a specific address.
    """

    def __init__(self, address: str, **criteria):
        super().__init__(address=address, **criteria)


class CoinbaseFilter(TxFilter):
    """
    Custom made filter to scan for coinbase transactions
    """

    def __init__(self, **criteria):
        super().__init__(coinbase=True, **criteria)


class CjFilter(TxFilter):
    """
    Custom made filter to scan for CoinJoin like transactions.
    Criteria:
    Number equal outputs >= 3
    Number inputs >= 3
    """

    def __init__(self, **criteria):
        super().__init__(n_eq=(3, 10000),
                         n_in=(3, 10000),
                         **criteria)


class WasabiFilter(TxFilter):
    """
    Custom made filter to scan for Wasabi like CoinJoin transactions.
    Criteria:
    N equal sized outputs where N >=5
    Number inputs >= 5
    Inputs and outputs type 'witness_v0_keyhash' (bech32)
    0.089 <= denomination <= 0.11
    """

    def __init__(self, **criteria):
        super().__init__(n_eq=(5, 10000),
                         n_in=(5, 10000),
                         den=(8900000, 11000000),
                         in_type='witness_v0_keyhash',
                         out_type='witness_v0_keyhash',
                         **criteria)


class JoinmarketFilter(TxFilter):
    """
    Custom made filter to scan for JoinMarket like CoinJoin transactions.
    Criteria:
    N equal sized outputs where N >=3 and N <= 40
    At least N inputs
    Either N or N-1 additional outputs of size different from the N equal outputs
    Inputs type 'scripthash' (P2SH) or 'witness_v0_keyhash' (bech32)
    Outputs type either all P2SH/bech32 or all P2SH/bech32 but one and the different one has to be an equal output
    """

    def __init__(self, **criteria):
        super().__init__(joinmarket=True,
                         **criteria,
                         )

    @staticmethod
    def match_joinmarket(tx: Tx) -> bool:
        # Cache n_eq
        n_eq: int = tx.n_eq
        # Number of equal output is capped to 40 mostly to eliminate Wasabi CoinJoins that match also
        # JoinMarket criteria. Since it is difficult/impossible to coordinate
        # such enourmous CoinJoin through IRC, this should not hide any real
        # JoinMarket transaction.
        # Few small Wasabi CoinJoins will of course still pass through, but
        # they should be rare and small enough to not poison the results.
        if not 3 <= n_eq <= 40:
            return False
        if not (tx.n_out in [n_eq * 2, n_eq * 2 - 1]):
            return False
        if not tx.n_in >= n_eq:
            return False
        # Only one equal output can have different type, we track it with this warning
        warning: int = 0
        # Remove 'scripthash' when P2SH inevitably gets obsolated.
        if tx.inputs[0].type not in ['scripthash', 'witness_v0_keyhash']:
            return False
        tx_type: str = tx.inputs[0].type
        for tx_input in tx.inputs[1:]:
            if tx_input.type != tx_type:
                return False
        for tx_out in tx.outputs:
            if tx_out.type != tx_type:
                if tx_out.value != tx.den:
                    return False
                if warning:
                    return False
                # Found a different equal output type
                warning += 1
        return True
