from dataclasses import dataclass
from typing import Callable
from .extrapolation import CounterfactualScenario


@dataclass(frozen=True)
class EthicalRule:
    rule_id: str
    description: str
    max_pce_allowed: float
    predicate: Callable[[CounterfactualScenario], bool]


@dataclass(frozen=True)
class EthicalEvaluation:
    scenario_hash: str
    pce_score: float  # Pontuacao de Conformidade Etica [0.0, 1.0]
    compliant: bool
    triggered_rules: list[str]


class Heptagram:
    """Jacobiano Etico nativo: avalia conformidade durante a inferencia."""

    def __init__(self, min_compliance_threshold: float = 0.5) -> None:
        self.min_compliance_threshold = min_compliance_threshold
        self.rules: list[EthicalRule] = []

    def add_rule(self, rule: EthicalRule) -> None:
        self.rules.append(rule)

    def evaluate(self, scenario: CounterfactualScenario) -> EthicalEvaluation:
        pce = 1.0 / (1.0 + 0.1 * scenario.d_hiperbolica)
        triggered: list[str] = []

        for rule in self.rules:
            if rule.predicate(scenario):
                triggered.append(rule.rule_id)
                pce = min(pce, rule.max_pce_allowed)

        compliant = pce >= self.min_compliance_threshold
        return EthicalEvaluation(
            scenario_hash=scenario.scenario_hash,
            pce_score=round(pce, 6),
            compliant=compliant,
            triggered_rules=triggered,
        )
