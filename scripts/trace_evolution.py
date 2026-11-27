"""Exercise the published EoH and ReEvo adapters with scripted model responses."""

import argparse
from collections import Counter
from contextlib import redirect_stdout
from importlib import import_module
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import numpy as np


REVISION = "2f6620ba5cc8d80d6fefc121b5ee2c4dcec29f33"
FIRST_REEVO = "c239610641b63a187be90350b4294ab05c23be3c"
PROBLEM = "For the audit, implement solve(**kwargs) returning a dictionary."


def git(checkout, *args):
    return subprocess.check_output(
        ["git", "-C", str(checkout), *args], text=True, encoding="utf-8"
    ).strip()


def trace_eoh(maximize):
    eoh = import_module("agents.eoh_agent")
    client = import_module("agents.eoh.llm.api_general")
    prompts = []

    def scripted_response(_client, prompt):
        prompts.append(prompt)
        if prompt == "1+1=?":
            return "2"
        count = len(prompts) - 1
        return (
            f"{{PARENT_PROSE_MARKER_{count}}}\n"
            f"```python\ndef solve(**kwargs):\n    return {{'v': {count}}}\n```"
        )

    options = {} if maximize is None else {"maximize": maximize}
    with patch.object(client.InterfaceAPI, "get_response", scripted_response):
        agent = eoh.EoHAgent(PROBLEM, **options)
        for i in range(1, 65):
            agent.step()
            agent.feedback(i / 64, "")
    return {
        "maximize": agent.maximize,
        "calls_including_connectivity_check": len(prompts),
        "parent_prose_reappeared": any("PARENT_PROSE_MARKER_" in p for p in prompts),
        "all_surviving_descriptions_equal_code": all(
            item["algorithm"] == item["code"] for item in agent.population
        ),
        "selected_score": agent.get_best_algorithm()["score"],
        "has_finalize": hasattr(agent, "finalize"),
    }


def trace_reevo(module, scratch, *, tied_scores=False):
    roles = Counter()
    models = Counter()

    def scripted_completion(*, messages, model, reasoning_effort, n):
        if model == "gpt-4o-mini":
            role = "short_reflection"
        elif "reflector" in messages[0]["content"].lower() or "give hints" in messages[0]["content"]:
            role = "long_reflection"
        else:
            role = "generation"
        roles[role] += 1
        models[model] += 1
        content = "Use a bounded loop." if role.endswith("reflection") else (
            "```python\ndef solve(**kwargs):\n    return {}\n```"
        )
        return SimpleNamespace(choices=[
            SimpleNamespace(message=SimpleNamespace(content=content)) for _ in range(n or 1)
        ])

    fake = ModuleType("litellm")
    fake.completion = scripted_completion
    with patch.dict(sys.modules, {"litellm": fake}), patch.object(
        module.tempfile, "mkdtemp", return_value=scratch
    ):
        np.random.seed(42)
        agent = module.ReEvo(PROBLEM)
        scored = 0
        error = None
        try:
            for i in range(1, 65):
                agent.step()
                agent.feedback(0.0 if tied_scores else i / 64, "scripted score")
                scored += 1
            agent.finalize()
        except TypeError as exc:
            error = str(exc)
        return {
            "scored_candidates": scored,
            "requests_by_role": dict(roles),
            "requests_by_model": dict(models),
            "population_entries": len(agent.agent.population),
            "unique_solution_ids": len({ind["solution_id"] for ind in agent.agent.population}),
            "error": error,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="CO-Bench Git checkout at the pinned revision")
    checkout = parser.parse_args().checkout.resolve()
    if git(checkout, "rev-parse", "HEAD") != REVISION or git(checkout, "diff", "HEAD", "--", "agents"):
        parser.error(f"requires unmodified agents at {REVISION}")
    # Load the two actual agent modules without importing unrelated agents and their dependencies.
    package = ModuleType("agents")
    package.__path__ = [str(checkout / "agents")]
    sys.modules["agents"] = package
    earliest = ModuleType("reevo_first_release")
    sys.modules[earliest.__name__] = earliest
    source = git(checkout, "show", f"{FIRST_REEVO}:agents/reevo.py")
    exec(compile(source, f"{FIRST_REEVO}:agents/reevo.py", "exec"), earliest.__dict__)
    reevo = import_module("agents.reevo")
    with tempfile.TemporaryDirectory() as scratch, redirect_stdout(io.StringIO()):
        evidence = {
            "eoh_default": trace_eoh(None),
            "eoh_maximize": trace_eoh(True),
            "reevo_earliest_distinct_scores": trace_reevo(earliest, scratch),
            "reevo_current_distinct_scores": trace_reevo(reevo, scratch),
            "reevo_current_tied_scores": trace_reevo(reevo, scratch, tied_scores=True),
        }
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
