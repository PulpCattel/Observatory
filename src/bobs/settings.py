"""
Module to handle settings file and object
"""

from typing import Optional, cast

from bobs.obs.criteria import CriterionField
from bobs.types import Toml
from marshmallow import fields
from marshmallow.schema import Schema
from toml import loads

SETTINGS_FILENAME = 'settings.toml'
BOBS_DEFAULT_SETTINGS = '''
# Bobs settings, refer to the documentation for more information

[general]
logging = "warning" # Possible values: "", "warning", "info"

[limits]
memory_limit = 80

[network]
endpoint = "http://127.0.0.1:8332"

[scan]
force = false

[filtering]
match_all = false # If `true`, when multiple filters are used, *all* have to match.

[favorites]
# Add here your favorite options, as you would type them in the command line, and give them a unique name.
# You can then just do, e.g., `bobs -fa jm` to use it.
jm = '-ddd -f joinmarket scan -s -100 -e 0'

[filters.coinbase]
is_coinbase = "Equal(True)"

[filters.txid]
txid = "Include('')" # Insert txid (or part of) between inner quotes.

[filters.address]
addresses = "Include('')" # Insert address between inner quotes.

[filters.huge_vsize]
vsize = "Greater(50000)"

[filters.huge_amount]
total_in = "Greater(1000*1e8)"
total_out = "Greater(1000*1e8)"

[filters.joinmarket]
n_eq = "Greater(3)"
_ = "Satisfy(lambda tx: tx.n_out in [tx.n_eq*2, tx.n_eq*2-1] and tx.n_in >= tx.n_eq)"

[filters.wasabi_legacy]
n_eq = "Greater(5)"
den = "Between(8900000, 11000000)"
_ = "Satisfy(lambda tx: tx.n_in >= tx.n_eq)"
__ = "Satisfy(lambda tx: all(t == 'witness_v0_keyhash' for t in tx.types))"
'''.strip()


class General(Schema):
    logging = fields.Str(required=True)


class Limits(Schema):
    memory_limit = fields.Int(required=True)


class Network(Schema):
    endpoint = fields.Str(required=True)


class Scan(Schema):
    force = fields.Bool(required=True)


class Filtering(Schema):
    match_all = fields.Bool(required=True)


class Settings(Schema):
    """
    Schema representation of the settings.toml configuration file
    """
    general = fields.Nested(General, required=True)
    limits = fields.Nested(Limits, required=True)
    network = fields.Nested(Network, required=True)
    scan = fields.Nested(Scan, required=True)
    filtering = fields.Nested(Filtering, required=True)
    favorites = fields.Dict(fields.Str(), fields.Str(), required=True)
    filters = fields.Dict(fields.Str(),
                          fields.Dict(fields.Str(),
                                      CriterionField()), required=True)

    @classmethod
    def from_default(cls) -> Toml:
        """
        Instantiate Settings object from BOBS_DEFAULT_SETTINGS
        """
        return cls.from_str(BOBS_DEFAULT_SETTINGS)

    @classmethod
    def from_str(cls, string: str) -> Toml:
        """
        Instantiate Settings object from TOML string representation
        """
        return cast(Toml, cls().load(loads(string)))

    @classmethod
    def from_file(cls, path: Optional[str] = None, force_exist: bool = False) -> Toml:
        """
        Deserialize Settings object from TOML file if found, else create one with
        BOBS_DEFAULT_SETTINGS.
        """
        try:
            with open(f'{path}/{SETTINGS_FILENAME}' if path else SETTINGS_FILENAME, 'r', encoding='utf-8') as file:
                return cls.from_str(file.read())
        except FileNotFoundError as err:
            if force_exist:
                raise err
            with open(f'{path}/{SETTINGS_FILENAME}' if path else SETTINGS_FILENAME, 'w', encoding='utf-8') as file:
                file.write(BOBS_DEFAULT_SETTINGS)
                return cls.from_default()
