from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from .layer0_hasher import CanonicalHasher, EdgeRecord, ImmutableIdentity, VertexRecord


@dataclass
class ShardPartition:
    shard_id: int
    vertices: dict[str, VertexRecord] = field(default_factory=dict)
    edges: dict[str, EdgeRecord] = field(default_factory=dict)


class ShardedGraphStore:
    """
    Armazenamento particionado por Sharding Canonico com Deduplicacao Natural,
    indices geodésicos O(1)/O(log N) e auditoria de integridade em background.
    """

    def __init__(self, hasher: CanonicalHasher) -> None:
        self.hasher = hasher
        self.shards: dict[int, ShardPartition] = {
            i: ShardPartition(shard_id=i) for i in range(hasher.num_shards)
        }
        self._incoming_index: dict[str, list[tuple[int, str]]] = defaultdict(list)
        self._outgoing_index: dict[str, list[tuple[int, str]]] = defaultdict(list)
        self.temporal_noise_stream: list[str] = []

    def ingest_vertex(
        self,
        identity: ImmutableIdentity,
        initial_state: dict[str, Any] | None = None,
    ) -> tuple[str, bool]:
        vid = self.hasher.hash_vertex(identity)
        sid = self.hasher.shard_for_hash(vid)
        part = self.shards[sid]

        if vid in part.vertices:
            if initial_state:
                part.vertices[vid].state.update(initial_state)
            return vid, False  # Deduplicacao natural: nao duplica entidade

        part.vertices[vid] = VertexRecord(
            id_canonico=vid,
            identity=identity,
            shard_id=sid,
            state=dict(initial_state or {}),
        )
        return vid, True

    def get_vertex(self, vertex_id: str) -> VertexRecord | None:
        sid = self.hasher.shard_for_hash(vertex_id)
        return self.shards[sid].vertices.get(vertex_id)

    def ingest_edge(
        self,
        origin_id: str,
        target_id: str,
        relation_type: str,
        causal_weight: float,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, bool]:
        if self.get_vertex(origin_id) is None or self.get_vertex(target_id) is None:
            raise KeyError("Origem e destino devem existir no grafo antes da aresta.")

        eid = self.hasher.hash_edge(origin_id, target_id, relation_type, causal_weight)
        sid = self.hasher.shard_for_hash(eid)
        part = self.shards[sid]

        if eid in part.edges:
            return eid, False  # Deduplicacao natural

        edge = EdgeRecord(
            id_aresta_canonica=eid,
            origin_id=origin_id,
            target_id=target_id,
            relation_type=relation_type,
            causal_weight=float(causal_weight),
            shard_id=sid,
            metadata=dict(metadata or {}),
        )
        part.edges[eid] = edge
        self._incoming_index[target_id].append((sid, eid))
        self._outgoing_index[origin_id].append((sid, eid))
        return eid, True

    def get_edge(self, edge_id: str) -> EdgeRecord | None:
        sid = self.hasher.shard_for_hash(edge_id)
        return self.shards[sid].edges.get(edge_id)

    def get_incoming_edges(self, target_id: str) -> list[EdgeRecord]:
        """Consulta topologica direta: ignora totalmente o stream de ruido temporal."""
        refs = self._incoming_index.get(target_id, [])
        return [self.shards[sid].edges[eid] for sid, eid in refs]

    def inject_temporal_noise(self, tokens: list[str]) -> int:
        self.temporal_noise_stream.extend(tokens)
        return len(self.temporal_noise_stream)

    def run_integrity_audit(self) -> list[str]:
        """Job de background (Secao 3.3.3): detecta corrupcao ou adulteracao de fatos."""
        corrupted_ids: list[str] = []
        for part in self.shards.values():
            for vid, v in part.vertices.items():
                if not self.hasher.verify_vertex_integrity(v):
                    corrupted_ids.append(vid)
            for eid, e in part.edges.items():
                if not self.hasher.verify_edge_integrity(e):
                    corrupted_ids.append(eid)
        return corrupted_ids
