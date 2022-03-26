"""
Module to scan Bitcoin data.
"""
from asyncio import run
from typing import Iterator

from bobs.network.rest import Rest
from bobs.obs.candidates import Candidate
from bobs.obs.targets import BlockTxsV3, MempoolTxsV3, Blocks, BlocksV3, MempoolTxs, MempoolTxsV2
from bobs.obs.utils import parse_start_and_end
from bobs.types import Toml, Filter, Json, BlockTarget, MemTarget
from tqdm import tqdm  # type: ignore[import] # No type-hinting


def scan_blocks(start: int,
                end: int,
                settings: Toml,
                candidate_id: str,
                *filters: Filter) -> Iterator[Candidate]:
    async def get_info(endpoint_: str) -> Json:
        async with Rest(endpoint=endpoint_) as rest:
            return await rest.get_info()

    endpoint: str = settings['network']['endpoint']
    info = run(get_info(endpoint))
    start, end = parse_start_and_end(start, end, info, settings['scan']['force'])
    target: BlockTarget
    if candidate_id == 'block':
        target = Blocks
    elif candidate_id == 'blockv3':
        target = BlocksV3
    elif candidate_id == 'txv3':
        target = BlockTxsV3
    else:
        raise ValueError(f'Invalid candidate {candidate_id}')
    with target(endpoint=endpoint, start=start, end=end) as target_:
        policy = all if settings['filtering']['match_all'] else any
        if not filters:
            # If no filters are selected, every candidate is yielded
            policy = all
        candidate: Candidate
        for candidate in tqdm(target_.candidates,
                              miniters=1,
                              mininterval=0.5,
                              total=end + 1 - start):
            if policy(map(candidate, filters)):
                yield candidate


def scan_mem(settings: Toml,
             candidate_id: str,
             *filters: Filter) -> Iterator[Candidate]:
    target: MemTarget
    if candidate_id == 'tx':
        target = MempoolTxs
    elif candidate_id == 'txv2':
        target = MempoolTxsV2
    elif candidate_id == 'txv3':
        target = MempoolTxsV3
    else:
        raise ValueError(f'Invalid candidate {candidate_id}')
    with target(endpoint=settings['network']['endpoint']) as target_:
        policy = all if settings['filtering']['match_all'] else any
        if not filters:
            policy = all
        candidate: Candidate
        for candidate in tqdm(target_.candidates):
            if policy(map(candidate, filters)):
                yield candidate
