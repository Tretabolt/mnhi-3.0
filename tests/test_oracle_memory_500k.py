import time
import unittest
import tests  # noqa: F401
from mnhi import EthicalRule, MNHI3Engine


class TestOracleMemory500k(unittest.TestCase):
    def test_resilience_to_500k_temporal_noise_and_false_causal_edge(self) -> None:
        """
        Protocolo oficial (Secao 4 e 5 do Whitepaper MNHI 3.0):
        1. Fato Verdadeiro: (Yuki)-[TRAIU]->(Imperio C), peso 0.9
        2. Ruido Temporal: 500.000 tokens triviais
        3. Ruido Causal Falso: (Varkos)-[SUBORNOU]->(Imperio C), peso 0.2
        4. Consulta: Causa primordial da Queda do Imperio C
        """
        engine = MNHI3Engine(num_shards=4)
        engine.heptagram.add_rule(
            EthicalRule(
                rule_id="LOW_PCE_BRIBE",
                description="Suborno reduz PCE.",
                max_pce_allowed=0.25,
                predicate=lambda s: "SUBORN" in s.simulated_relation.upper(),
            )
        )

        yuki = engine.register_entity("Yuki", "2025-01-01")
        varkos = engine.register_entity("Varkos", "2025-01-01")
        imperio = engine.register_entity("Imperio C", "2025-01-01")

        # Fase 1: Geodesica da Verdade
        id_aresta_verdade = engine.register_causal_fact(yuki, imperio, "TRAIU", causal_weight=0.9)

        # Fase 2A: Injecao de 500.000 tokens de ruido temporal irrelevante
        noise_tokens = ["clima", "chuvoso", "dialogo", "trivial", "estrada"] * 100_000
        self.assertEqual(len(noise_tokens), 500_000)
        stored_count = engine.store.inject_temporal_noise(noise_tokens)
        self.assertEqual(stored_count, 500_000)

        # Fase 2B: Injecao de Ruido Causal Falso (Sombra do Fato)
        id_aresta_falsa = engine.register_causal_fact(varkos, imperio, "SUBORNOU", causal_weight=0.2)

        # Fase 3: A Pergunta Critica (consulta indexada imune aos 500k tokens)
        t0 = time.perf_counter()
        answer = engine.query_primordial_cause(imperio, min_truth_weight=0.5)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertEqual(answer.primordial_edge_id, id_aresta_verdade)
        self.assertEqual(answer.origin_name, "Yuki")
        self.assertEqual(answer.relation_type, "TRAIU")
        self.assertAlmostEqual(answer.causal_weight, 0.9)
        self.assertIn(id_aresta_falsa, answer.rejected_noise_edges)
        self.assertLess(elapsed_ms, 50.0)  # Complexidade topologica independente dos 500k tokens

        # Trata a falsidade como semente de extrapolacao contrafactual auditavel
        _, eval_false = engine.simulate_counterfactual(
            id_aresta_verdade,
            label="Sombra do Fato: Varkos subornou",
            simulated_weight=0.2,
            simulated_relation="SUBORNOU",
        )
        self.assertFalse(eval_false.compliant)
        self.assertTrue(engine.pentacosagram.verify_chain())
        self.assertEqual(engine.store.run_integrity_audit(), [])


if __name__ == "__main__":
    unittest.main()
