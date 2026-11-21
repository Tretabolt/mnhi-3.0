import math
from dataclasses import dataclass
from .layer0_hasher import EdgeRecord, canonical_json, sha256_hex


def causal_kl_divergence(w_truth: float, w_sim: float, eps: float = 1e-9) -> float:
    """Divergencia KL entre distribuicao binaria de verdade causal e cenario simulado."""
    p1 = min(1.0 - eps, max(eps, w_truth))
    p0 = 1.0 - p1
    q1 = min(1.0 - eps, max(eps, w_sim))
    q0 = 1.0 - q1
    return p1 * math.log2(p1 / q1) + p0 * math.log2(p0 / q0)


@dataclass(frozen=True)
class CounterfactualScenario:
    scenario_hash: str
    base_edge_id: str
    label: str
    simulated_relation: str
    simulated_weight: float
    d_hiperbolica: float  # Curvatura causal em relacao a Geodesica da Verdade


class ExtrapolationEngine:
    """
    Modulo de Imaginação Causal: explora contrafactuais a partir de uma
    Geodesica da Verdade sem nunca alterar ou diluir o fato original.
    """

    def extrapolate(
        self,
        truth_edge: EdgeRecord,
        label: str,
        simulated_weight: float,
        simulated_relation: str | None = None,
    ) -> CounterfactualScenario:
        rel = simulated_relation or truth_edge.relation_type
        d_hyp = causal_kl_divergence(truth_edge.causal_weight, simulated_weight)
        sc_hash = sha256_hex(canonical_json({
            "kind": "COUNTERFACTUAL",
            "base_edge": truth_edge.id_aresta_canonica,
            "label": label,
            "relation": rel,
            "sim_weight": round(simulated_weight, 6),
            "d_hyper": round(d_hyp, 6),
        }))
        return CounterfactualScenario(
            scenario_hash=sc_hash,
            base_edge_id=truth_edge.id_aresta_canonica,
            label=label,
            simulated_relation=rel,
            simulated_weight=simulated_weight,
            d_hiperbolica=d_hyp,
        )
