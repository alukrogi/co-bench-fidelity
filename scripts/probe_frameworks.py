"""Offline control-flow probes for the pinned CO-Bench release (Python 3.11+)."""

import argparse
from collections import Counter
from contextlib import redirect_stdout
from importlib import import_module
import io
import json
from pathlib import Path
import random
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import numpy as np


REVISION = "2f6620ba5cc8d80d6fefc121b5ee2c4dcec29f33"


def use_package(name, path):
    """Skip eager optional-agent imports in the upstream package initializers."""
    module = ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module


class FixtureClient:
    def __init__(self):
        self.calls = 0

    def chat_completion(self, *args, **kwargs):
        self.calls += 1
        # A unique, parseable model response. No generated program is executed.
        content = f"{{fixture {self.calls}}}\n```python\ndef solve(**kwargs):\n    return {self.calls}\n```"
        return [SimpleNamespace(message=SimpleNamespace(content=content))]


def probe_mcts(repository):
    use_package("agents.mcts", repository / "agents/mcts")
    client = FixtureClient()
    transport = ModuleType("agents.mcts.utils.utils")
    transport.init_client = lambda config: client
    sys.modules[transport.__name__] = transport
    module = import_module("agents.mcts_agent")
    # Divert intermediate JSON population dumps without modifying the checkout.
    module.open = lambda filename, mode: io.StringIO()
    wrapper = module.MctsAhd
    scores = list(range(1, 65))
    random.Random(487).shuffle(scores)
    operators = Counter()
    missing_parent = 0
    with redirect_stdout(io.StringIO()):
        agent = wrapper("fixture", max_fe=64)
        for score in scores:
            code = agent.step()
            assert code and agent.pending_algorithm != "Fallback heuristic"
            operator = agent.pending_operator
            operators[operator] += 1
            if operator == "e2" and agent.pending_node.raw_info not in agent.pending_parents:
                missing_parent += 1
            agent.feedback(score / 64)
        assert agent.step() is None
        assert agent.get_best_score() == 1
        assert sum(operators.values()) == 64 and set(operators) == {"i1", "e1", "e2"}
        assert missing_parent > 0
        calls_on_positive_fixture = client.calls
        zero_agent = wrapper("fixture", max_fe=64)
        for _ in range(4):
            zero_agent.step()
            zero_agent.feedback(0.0)
        try:
            zero_agent.step()
        except ZeroDivisionError:
            zero_outcome = "ZeroDivisionError"
        else:
            raise AssertionError("Expected the UCT zero-range condition after four zero scores")
    return {
        "evaluated_candidates": len(scores),
        "fixture_model_calls": calls_on_positive_fixture,
        "operator_counts": dict(sorted(operators.items())),
        "e2_prompts_omitting_selected_tree_parent": missing_parent,
        "step_5_after_four_zero_scores": zero_outcome,
    }


def probe_funsearch():
    model = import_module("agents.funsearch_agent.model")
    island = model.Island("fixture", functions_per_prompt=2)
    # Each pair is an artificial two-instance performance profile.
    cases = {"A": (0.0, 1.0), "B": (1.0, 0.0), "C": (0.6, 0.6), "D": (0.7, 0.7)}
    for label, scores in cases.items():
        solution = model.Solution(f"fixture_{label}")
        solution.score_detail = str(scores)
        island.register_solution(solution, sum(scores) / len(scores))
    support = set()
    for _ in range(100):
        prompt, _ = island.get_prompt()
        support.add(tuple(label for label in cases if f"fixture_{label}" in prompt))
    assert len(island.clusters) == 3 and support == {("C", "D")}
    return {
        "distinct_profiles": len(cases),
        "registered_clusters": len(island.clusters),
        "prompt_exemplars_in_100_draws": sorted(support),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("co_bench_checkout", type=Path)
    args = parser.parse_args()
    repository = args.co_bench_checkout.resolve()
    revision = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != REVISION:
        parser.error(f"Checkout {REVISION} before running this revision-specific probe")
    random.seed(487)
    np.random.seed(487)
    sys.dont_write_bytecode = True
    use_package("agents", repository / "agents")
    result = {"revision": revision, "funsearch": probe_funsearch(), "mcts_ahd": probe_mcts(repository)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
