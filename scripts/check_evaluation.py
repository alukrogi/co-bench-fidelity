"""Reproduce the release, split, label, weighting and scheduling-reference checks."""

import argparse
import ast
import json
import math
from pathlib import Path
import runpy

from fetch_evaluation_inputs import APRIL, AUGUST, REVISION


def scoring_functions(repo):
    # Extract the three unmodified pure functions. The upstream module also
    # imports POSIX process-control and LLM packages that these checks do not use.
    path = repo / "evaluation" / "utils.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {"filter_dev", "filter_test", "average_score"}
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {}
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace


def split_inventory(data, scoring):
    configs = sorted(data.glob("*/config.py"))
    if len(configs) != 36:
        raise ValueError(f"Expected 36 task configurations, found {len(configs)}")
    overlaps = {}
    for path in configs:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.FunctionDef) and n.name == "get_dev" for n in tree.body):
            continue
        cfg = runpy.run_path(str(path))
        groups = {}
        for case in sorted(path.parent.glob("*.txt")):
            count = len(cfg["load_data"](str(case)))
            groups[case.name] = (list(range(count)), None)
        if not groups:
            raise ValueError(f"Missing data for {path.parent.name}")
        assert scoring["filter_dev"](groups, None) == scoring["filter_test"](groups, None) == groups
        overlaps[path.parent.name] = sum(len(scores) for scores, _ in groups.values())
    return overlaps


def tsp_check(data, scoring):
    folder = data / "Travelling salesman problem"
    cfg = runpy.run_path(str(folder / "config.py"))
    labels = {}
    groups = {}
    for path in sorted(folder.glob("*.txt")):
        lengths = []
        for inst in cfg["load_data"](str(path)):
            tour = inst["label_tour"]
            points = inst["nodes"]
            assert sorted(tour) == list(range(len(points)))
            lengths.append(sum(math.dist(points[a], points[b]) for a, b in zip(tour, tour[1:] + tour[:1])))
        ratios = cfg["norm_score"]({path.name: (lengths, None)})[path.name][0]
        labels[path.name] = {"instances": len(lengths), "min_length": min(lengths),
                             "max_length": max(lengths), "min_ref_ratio": min(ratios),
                             "max_ref_ratio": max(ratios),
                             "within_1e-10_of_reference": sum(abs(x - 1) < 1e-10 for x in ratios)}
        indicator = int(path.name == "tsp10000_test_concorde.txt")
        groups[path.name] = ([indicator] * len(lengths), None)
    file_weight = scoring["average_score"](groups, list(groups))
    all_scores = [s for scores, _ in groups.values() for s in scores]
    return {"labels": labels, "tsp10000_weight_in_release": file_weight,
            "tsp10000_weight_per_instance": sum(all_scores) / len(all_scores)}


def scheduling_check(data):
    results = {}
    for task in ("Flow shop scheduling", "Job shop scheduling", "Open shop scheduling"):
        folder = data / task
        config = runpy.run_path(str(folder / "config.py"))
        dev = config["get_dev"]()
        heldout = []
        for case in sorted(folder.glob("*.txt")):
            for idx, inst in enumerate(config["load_data"](str(case))):
                if idx not in dev.get(case.name, []):
                    heldout.append((inst["lower_bound"], inst["upper_bound"]))
        results[task] = {"held_out": len(heldout), "distinct_bounds": sum(l != u for l, u in heldout),
                         "file_upper_would_score_below_.99": sum(l / u < .99 for l, u in heldout)}
    return results


def historical_checks(data, scoring):
    trees = [json.loads((data / f"tree-{rev}.json").read_text(encoding="utf-8"))
             for rev in (APRIL, AUGUST, REVISION)]
    changes = []
    for earlier, later in zip(trees, trees[1:]):
        changes.append({"earlier_files": len(earlier), "later_files": len(later),
                        "changed_common_configs": sorted(
                            k for k in earlier.keys() & later.keys() if
                            k.endswith("/config.py") and earlier[k] != later[k]),
                        "added_MIS_validation_graphs": sum(
                            k.startswith("Maximal independent set/er_valid/")
                            for k in later.keys() - earlier.keys())})
    shared_geometry = {}
    for task in ("Packing unequal circles", "Packing unequal rectangles and squares"):
        files = [key for key in trees[-1] if key.startswith(task + "/") and key.endswith(".txt")]
        shared_geometry[task] = sum(trees[-1][key] == trees[-1][key.replace(task + "/", task + " area/", 1)]
                                    for key in files)
    folder = data / "Packing unequal circles area"
    earlier = runpy.run_path(str(data / "april" / folder.name / "config.py"))
    groups = {p.name: (list(range(len(earlier["load_data"](str(p))))), None)
              for p in sorted(folder.glob("*.txt"))}
    old_test = scoring["filter_test"](groups, earlier["get_dev"]())
    # Illustrate the historical normalization with a numeric value twice
    # the 305 reference. This tests the transform, independently of a solver.
    probe = {"assign100.txt": ([610.0], None)}
    ratios = []
    for root in (data / "april", data):
        cfg = runpy.run_path(str(root / "Assignment problem" / "config.py"))
        ratios.append(cfg["norm_score"](probe)["assign100.txt"][0][0])
    return {"file_tree_changes": changes, "identical_raw_files_in_area_variant": shared_geometry,
            "april_circle_area_test_files": len(old_test),
            "assignment_2x_reference_normalized_april_current": ratios}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("repo", type=Path)
    args = parser.parse_args()
    scoring = scoring_functions(args.repo)
    results = {"shared_dev_test_instances": split_inventory(args.data, scoring),
               "tsp": tsp_check(args.data, scoring), "scheduling": scheduling_check(args.data),
               "historical": historical_checks(args.data, scoring)}
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
