"""
Collection of custom types and aliases.
"""

from typing import Dict, Union, Any, Mapping, TYPE_CHECKING, Type

if TYPE_CHECKING:
    # Avoid circular import
    from bobs.obs.criteria import Criterion
    from bobs.obs.targets import Blocks, BlockTxsV3, BlocksV3, MempoolTxs, MempoolTxsV2, MempoolTxsV3
# For Python 3.8 compatibility, see https://mypy.readthedocs.io/en/latest/kinds_of_types.html#type-aliases
from typing_extensions import TypeAlias

# Argument for REST URI
RestUriArg: TypeAlias = Union[int, str]

# Bytes-like
Bytes: TypeAlias = Union[bytes, bytearray]

# A filter which holds a mapping of ID and Criteria
Filter: TypeAlias = Dict[str, 'Criterion']

# Either of the Target which targets blocks
BlockTarget: TypeAlias = Union[Type['Blocks'], Type['BlocksV3'], Type['BlockTxsV3']]

# Either of the Target which targets the mempool
MemTarget: TypeAlias = Union[Type['MempoolTxs'], Type['MempoolTxsV2'], Type['MempoolTxsV3']]

# Dynamic Types
# Those types below are the only one allowed to have Any explicitly
# TODO: restrict these

# To be used rarely only for extremely generic types, use this instead of Any directly.
Any_: TypeAlias = Any

# An hypothesis draw() SearchStrategy.
# TODO: specify exact type
DrawObject = Any_

# Settings file, generated from parsing TOML
Toml: TypeAlias = Mapping[str, Any_]

# JSON, mostly generated by Bitcoin Core server
Json: TypeAlias = Dict[str, Any_]

# Raw data for Candidate objects
RawData: TypeAlias = Mapping[str, Any_]
