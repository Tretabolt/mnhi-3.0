import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


MUTABLE_STATE_EXCLUSIONS = frozenset({
    "estado_emocional",
    "localizacao",
    "saude",
    "humor",
    "posicao",
    "timestamp_leitura",
})


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ImmutableIdentity:
    name: str
    data_criacao: str
    entity_type: str = "ENTIDADE"
    extra_immutable: tuple[tuple[str, str], ...] = ()


@dataclass
class VertexRecord:
    id_canonico: str
    identity: ImmutableIdentity
    shard_id: int
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeRecord:
    id_aresta_canonica: str
    origin_id: str
    target_id: str
    relation_type: str
    causal_weight: float
    shard_id: int
    metadata: dict[str, Any] = field(default_factory=dict)


class CanonicalHasher:
    """Camada 0 do MNHI 3.0: Identidade Imutavel, Cadeia de Custodia e Sharding."""

    def __init__(self, num_shards: int = 4, prefix_bits: int = 16) -> None:
        if num_shards < 1:
            raise ValueError("num_shards deve ser >= 1")
        self.num_shards = num_shards
        self.prefix_bits = prefix_bits

    def hash_vertex(self, identity: ImmutableIdentity) -> str:
        for k, _ in identity.extra_immutable:
            if k in MUTABLE_STATE_EXCLUSIONS:
                raise ValueError(f"Atributo mutavel '{k}' proibido no calculo de id_canonico.")
        payload = {
            "kind": "VERTEX",
            "name": identity.name,
            "data_criacao": identity.data_criacao,
            "entity_type": identity.entity_type,
            "extra": dict(identity.extra_immutable),
        }
        return sha256_hex(canonical_json(payload))

    def hash_edge(
        self,
        origin_id: str,
        target_id: str,
        relation_type: str,
        causal_weight: float,
    ) -> str:
        if not origin_id or not target_id or not relation_type:
            raise ValueError("origin_id, target_id e relation_type sao obrigatorios.")
        payload = {
            "kind": "EDGE",
            "origin": origin_id,
            "target": target_id,
            "type": relation_type,
            "peso": round(float(causal_weight), 6),
        }
        return sha256_hex(canonical_json(payload))

    def shard_for_hash(self, canonical_hash: str) -> int:
        hex_chars = max(1, self.prefix_bits // 4)
        prefix_val = int(canonical_hash[:hex_chars], 16)
        return prefix_val % self.num_shards

    def verify_vertex_integrity(self, vertex: VertexRecord) -> bool:
        return self.hash_vertex(vertex.identity) == vertex.id_canonico

    def verify_edge_integrity(self, edge: EdgeRecord) -> bool:
        return (
            self.hash_edge(
                edge.origin_id,
                edge.target_id,
                edge.relation_type,
                edge.causal_weight,
            )
            == edge.id_aresta_canonica
        )
