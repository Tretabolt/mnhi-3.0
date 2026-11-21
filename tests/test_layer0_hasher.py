import unittest
import tests  # noqa: F401
from mnhi.layer0_hasher import CanonicalHasher, ImmutableIdentity
from mnhi.graph_store import ShardedGraphStore


class TestLayer0CanonicalHasher(unittest.TestCase):
    def test_identity_remains_immutable_across_state_changes(self) -> None:
        hasher = CanonicalHasher(num_shards=4)
        store = ShardedGraphStore(hasher)

        yuki_id_struct = ImmutableIdentity(name="Yuki", data_criacao="2025-01-01")
        id1, created1 = store.ingest_vertex(yuki_id_struct, {"estado_emocional": "alegre", "localizacao": "Torre"})
        id2, created2 = store.ingest_vertex(yuki_id_struct, {"estado_emocional": "grata", "localizacao": "Porto"})

        self.assertTrue(created1)
        self.assertFalse(created2)  # Deduplicacao natural evitou duplicar Yuki!
        self.assertEqual(id1, id2)
        self.assertEqual(store.get_vertex(id1).state["estado_emocional"], "grata")

    def test_rejects_mutable_attribute_in_identity(self) -> None:
        hasher = CanonicalHasher()
        bad = ImmutableIdentity(name="Yuki", data_criacao="2025-01-01", extra_immutable=(("estado_emocional", "alegre"),))
        with self.assertRaises(ValueError):
            hasher.hash_vertex(bad)

    def test_integrity_audit_detects_tampering(self) -> None:
        hasher = CanonicalHasher(num_shards=4)
        store = ShardedGraphStore(hasher)

        a = store.ingest_vertex(ImmutableIdentity(name="Yuki", data_criacao="2025-01-01"))[0]
        c = store.ingest_vertex(ImmutableIdentity(name="Imperio C", data_criacao="2025-01-01"))[0]
        eid, _ = store.ingest_edge(a, c, "TRAIU", 0.9)

        self.assertEqual(store.run_integrity_audit(), [])

        # Adultera peso sem alterar id_aresta_canonica
        store.get_edge(eid).causal_weight = 0.1
        corrupted = store.run_integrity_audit()
        self.assertEqual(corrupted, [eid])


if __name__ == "__main__":
    unittest.main()
