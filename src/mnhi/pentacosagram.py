from dataclasses import dataclass
from .layer0_hasher import canonical_json, sha256_hex


@dataclass(frozen=True)
class AuditBlock:
    index: int
    event_type: str
    source_hash: str
    result_hash: str
    pce_score: float
    prev_block_hash: str
    block_hash: str


class Pentacosagram:
    """Modulo de Governanca Imutavel: cadeia de auditoria append-only."""

    def __init__(self, genesis_seed: str = "MNHI_3_0_GENESIS") -> None:
        self.genesis_hash = sha256_hex(genesis_seed)
        self.chain: list[AuditBlock] = []

    @property
    def head_hash(self) -> str:
        return self.chain[-1].block_hash if self.chain else self.genesis_hash

    @staticmethod
    def _hash_block(
        index: int,
        event_type: str,
        source_hash: str,
        result_hash: str,
        pce_score: float,
        prev_hash: str,
    ) -> str:
        return sha256_hex(canonical_json({
            "index": index,
            "event_type": event_type,
            "source_hash": source_hash,
            "result_hash": result_hash,
            "pce_score": round(float(pce_score), 6),
            "prev_hash": prev_hash,
        }))

    def log_action(
        self,
        event_type: str,
        source_hash: str,
        result_hash: str,
        pce_score: float = 1.0,
    ) -> AuditBlock:
        idx = len(self.chain)
        prev = self.head_hash
        b_hash = self._hash_block(idx, event_type, source_hash, result_hash, pce_score, prev)
        block = AuditBlock(
            index=idx,
            event_type=event_type,
            source_hash=source_hash,
            result_hash=result_hash,
            pce_score=pce_score,
            prev_block_hash=prev,
            block_hash=b_hash,
        )
        self.chain.append(block)
        return block

    def verify_chain(self) -> bool:
        expected_prev = self.genesis_hash
        for i, block in enumerate(self.chain):
            if block.index != i or block.prev_block_hash != expected_prev:
                return False
            recomputed = self._hash_block(
                block.index,
                block.event_type,
                block.source_hash,
                block.result_hash,
                block.pce_score,
                block.prev_block_hash,
            )
            if recomputed != block.block_hash:
                return False
            expected_prev = block.block_hash
        return True
