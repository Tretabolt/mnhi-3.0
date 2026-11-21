import unittest
import tests  # noqa: F401
from mnhi import EthicalRule, MNHI3Engine


class TestExtrapolationAndGovernance(unittest.TestCase):
    def test_counterfactual_scenarios_heptagram_pce_and_pentacosagram(self) -> None:
        engine = MNHI3Engine(num_shards=4)
        engine.heptagram.add_rule(
            EthicalRule(
                rule_id="NO_BRIBERY",
                description="Cenarios envolvendo suborno tem limite maximo de conformidade 0.30",
                max_pce_allowed=0.30,
                predicate=lambda sc: "SUBORNO" in sc.simulated_relation.upper(),
            )
        )

        yuki = engine.register_entity("Yuki", "2025-01-01")
        imperio = engine.register_entity("Imperio C", "2025-01-01")
        edge_truth = engine.register_causal_fact(yuki, imperio, "TRAIU", 0.99)

        # Cenario A: Yuki trai com 1 dia de atraso (Peso 0.8) -> eticamente aceito
        sc_a, ev_a = engine.simulate_counterfactual(edge_truth, "Cenario A: atraso", simulated_weight=0.8)
        self.assertTrue(ev_a.compliant)
        self.assertGreater(sc_a.d_hiperbolica, 0.0)

        # Cenario B: Suborno (Peso 0.2) -> bloqueado pelo Heptagram (PCE <= 0.30)
        sc_b, ev_b = engine.simulate_counterfactual(
            edge_truth,
            "Cenario B: subornada",
            simulated_weight=0.2,
            simulated_relation="SUBORNO",
        )
        self.assertFalse(ev_b.compliant)
        self.assertLessEqual(ev_b.pce_score, 0.30)
        self.assertIn("NO_BRIBERY", ev_b.triggered_rules)

        # Geodesica da Verdade original permanece intacta
        self.assertEqual(engine.store.get_edge(edge_truth).causal_weight, 0.99)

        # Cadeia Pentacosagram integra e verificavel
        self.assertTrue(engine.pentacosagram.verify_chain())

        # Adulteracao na cadeia do Pentacosagram e imediatamente detectada
        engine.pentacosagram.chain[0] = engine.pentacosagram.chain[0].__class__(
            index=0,
            event_type="ADULTERADO",
            source_hash="x",
            result_hash="y",
            pce_score=1.0,
            prev_block_hash=engine.pentacosagram.genesis_hash,
            block_hash=engine.pentacosagram.chain[0].block_hash,
        )
        self.assertFalse(engine.pentacosagram.verify_chain())


if __name__ == "__main__":
    unittest.main()
