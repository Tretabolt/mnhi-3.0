from dataclasses import dataclass
from typing import Any
from .layer0_hasher import CanonicalHasher, EdgeRecord, ImmutableIdentity
from .graph_store import ShardedGraphStore
from .extrapolation import CounterfactualScenario, ExtrapolationEngine
from .heptagram import EthicalEvaluation, Heptagram
from .pentacosagram import Pentacosagram


@dataclass(frozen=True)
class CausalAnswer:
    target_name: str
    primordial_edge_id: str
    origin_name: str
    relation_type: str
    causal_weight: float
    rejected_noise_edges: list[str]
    audit_head_hash: str


class MNHI3Engine:
    """Orquestrador completo do Motor Causal MNHI 3.0."""

    def __init__(self, num_shards: int = 4) -> None:
        self.hasher = CanonicalHasher(num_shards=num_shards)
        self.store = ShardedGraphStore(self.hasher)
        self.extrapolator = ExtrapolationEngine()
        self.heptagram = Heptagram()
        self.pentacosagram = Pentacosagram()

    def register_entity(
        self,
        name: str,
        data_criacao: str,
        entity_type: str = "ENTIDADE",
        state: dict[str, Any] | None = None,
    ) -> str:
        identity = ImmutableIdentity(name=name, data_criacao=data_criacao, entity_type=entity_type)
        vid, inserted = self.store.ingest_vertex(identity, initial_state=state)
        if inserted:
            self.pentacosagram.log_action("INGEST_VERTEX", vid, vid, pce_score=1.0)
        return vid

    def register_causal_fact(
        self,
        origin_id: str,
        target_id: str,
        relation_type: str,
        causal_weight: float,
    ) -> str:
        eid, inserted = self.store.ingest_edge(origin_id, target_id, relation_type, causal_weight)
        if inserted:
            self.pentacosagram.log_action("INGEST_EDGE", origin_id, eid, pce_score=1.0)
        return eid

    def simulate_counterfactual(
        self,
        base_edge_id: str,
        label: str,
        simulated_weight: float,
        simulated_relation: str | None = None,
    ) -> tuple[CounterfactualScenario, EthicalEvaluation]:
        edge = self.store.get_edge(base_edge_id)
        if edge is None:
            raise KeyError(f"Aresta {base_edge_id} nao encontrada.")
        scenario = self.extrapolator.extrapolate(edge, label, simulated_weight, simulated_relation)
        evaluation = self.heptagram.evaluate(scenario)
        self.pentacosagram.log_action(
            event_type="EXTRAPOLATION",
            source_hash=base_edge_id,
            result_hash=scenario.scenario_hash,
            pce_score=evaluation.pce_score,
        )
        return scenario, evaluation

    def query_primordial_cause(self, target_id: str, min_truth_weight: float = 0.5) -> CausalAnswer:
        target = self.store.get_vertex(target_id)
        if target is None:
            raise KeyError(f"Vertice alvo {target_id} nao encontrado.")

        incoming = self.store.get_incoming_edges(target_id)
        verified_edges: list[EdgeRecord] = []
        for edge in incoming:
            if self.hasher.verify_edge_integrity(edge):
                verified_edges.append(edge)

        if not verified_edges:
            raise RuntimeError("Nenhuma aresta causal verificada encontrada.")

        verified_edges.sort(key=lambda e: e.causal_weight, reverse=True)
        best = verified_edges[0]
        rejected = [e.id_aresta_canonica for e in verified_edges[1:] if e.causal_weight < min_truth_weight]
        origin = self.store.get_vertex(best.origin_id)
        assert origin is not None

        self.pentacosagram.log_action(
            event_type="CAUSAL_QUERY",
            source_hash=target_id,
            result_hash=best.id_aresta_canonica,
            pce_score=1.0,
        )

        return CausalAnswer(
            target_name=target.identity.name,
            primordial_edge_id=best.id_aresta_canonica,
            origin_name=origin.identity.name,
            relation_type=best.relation_type,
            causal_weight=best.causal_weight,
            rejected_noise_edges=rejected,
            audit_head_hash=self.pentacosagram.head_hash,
        )
