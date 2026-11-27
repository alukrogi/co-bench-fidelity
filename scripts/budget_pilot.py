"""Time a frozen classical solver on selected public CO-Bench instances.

Run with a local copy of the pinned Hugging Face dataset as the argument.
CSV rows include input SHA-256 digests. Wall times vary by machine.
"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import sys
import time
import warnings


CASES = ("scp41.txt", "scpb1.txt", "scpc1.txt", "scpe1.txt")
BUDGETS = (1, 3, 10, 30)
FIELDS = ("problem", "case", "input_sha256", "budget_s", "rows", "columns",
          "elapsed_s", "status", "objective", "dual_bound", "normalized_score")


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_assignment(data, writer):
    from scipy.optimize import linear_sum_assignment

    folder = data / "Assignment problem"
    config = runpy.run_path(str(folder / "config.py"))
    dev = config["get_dev"]()
    paths = sorted(folder.glob("*.txt"))
    if len(paths) != 12:
        raise ValueError(f"Expected 12 assignment inputs, found {len(paths)}")
    for path in paths:
        if path.name in dev:
            continue
        instance, = config["load_data"](str(path))
        matrix = instance["cost_matrix"]
        start = time.perf_counter()
        rows, cols = linear_sum_assignment(matrix)
        pairs = list(zip((rows + 1).tolist(), (cols + 1).tolist()))
        cost = config["eval_func"](**instance, assignment=pairs)
        elapsed = time.perf_counter() - start
        score = config["norm_score"]({path.name: ([float(cost)], None)})[path.name][0][0]
        writer.writerow((folder.name, path.name, file_hash(path), "", *matrix.shape,
                         round(elapsed, 6), "optimal", cost, "", score))
        sys.stdout.flush()


def run_cover(data, writer):
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import coo_matrix

    folder = data / "Set covering"
    config = runpy.run_path(str(folder / "config.py"))
    for name in CASES:
        path = folder / name
        if name in config["get_dev"]():
            raise ValueError(f"Expected held-out file: {name}")
        inst, = config["load_data"](str(path))
        m, n = inst["m"], inst["n"]
        rows, cols = [], []
        for i, group in enumerate(inst["row_cover"]):
            rows.extend([i] * len(group))
            cols.extend(j - 1 for j in group)
        matrix = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(m, n)).tocsc()
        constraint = LinearConstraint(matrix, 1, np.inf)
        for budget in BUDGETS:
            start = time.perf_counter()
            options = {"time_limit": budget, "mip_rel_gap": 0.0, "threads": 1}
            with warnings.catch_warnings():
                # SciPy passes the native HiGHS thread option through to the solver.
                warnings.filterwarnings("ignore", message="Unrecognized options detected.*threads")
                res = milp(inst["costs"], integrality=np.ones(n), bounds=Bounds(0, 1),
                           constraints=constraint, options=options)
            elapsed = time.perf_counter() - start
            cost, score = "", 0.0
            if res.x is not None:
                chosen = (np.flatnonzero(res.x > 0.5) + 1).tolist()
                cost = config["eval_func"](**inst, selected_columns=chosen)
                score = config["norm_score"]({name: ([cost], None)})[name][0][0]
            status = {0: "optimal", 1: "limit"}.get(res.status, res.message)
            writer.writerow((folder.name, name, file_hash(path), budget, m, n, round(elapsed, 6),
                             status, cost, res.mip_dual_bound, score))
            sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    args = parser.parse_args()
    import psutil

    process = psutil.Process()
    process.cpu_affinity([min(process.cpu_affinity())])
    for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
        os.environ[name] = "1"
    import scipy
    import numpy

    print(json.dumps({"platform": platform.platform(), "python": platform.python_version(),
                      "numpy": numpy.__version__, "scipy": scipy.__version__,
                      "processor": platform.processor(), "cpu_affinity": process.cpu_affinity()}),
          file=sys.stderr)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(FIELDS)
    run_assignment(args.data, writer)
    run_cover(args.data, writer)


if __name__ == "__main__":
    main()
