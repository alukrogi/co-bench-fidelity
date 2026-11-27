"""Replay or verify paired anytime measurements on six public Taillard instances."""

import argparse
import hashlib
import json
import os
import platform
import random
import runpy
import time
from pathlib import Path

FILES = ("tai20_5.txt", "tai50_10.txt", "tai100_20.txt")
BUDGETS = (1, 10, 30)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def makespan(order, matrix):
    machine_end = [0] * len(matrix[0])
    for job in order:
        previous = 0
        for machine, duration in enumerate(matrix[job]):
            previous = max(previous, machine_end[machine]) + duration
            machine_end[machine] = previous
    return machine_end[-1]


def search(matrix):
    rng = random.Random(0)
    started = time.perf_counter()
    cpu_start = time.process_time()
    history = []
    initial = list(range(len(matrix)))

    def observe(order):
        value = makespan(order, matrix)
        if not history or value < history[-1]["makespan"]:
            history.append(dict(makespan=value, permutation=[j + 1 for j in order],
                                elapsed=time.perf_counter() - started,
                                cpu=time.process_time() - cpu_start))
        return value

    observe(initial)
    current = []
    for job in sorted(initial, key=lambda j: -sum(matrix[j])):
        positions = (current[:i] + [job] + current[i:] for i in range(len(current) + 1))
        current = min(positions, key=lambda p: makespan(p, matrix))
    current_cost = observe(current)
    neh = dict(makespan=current_cost, elapsed=time.perf_counter() - started)
    steps = 0
    while time.perf_counter() - started < max(BUDGETS):
        candidate = current.copy()
        if steps and steps % 250 == 0:
            candidate = [j - 1 for j in history[-1]["permutation"]]
            for _ in range(3):
                i, j = rng.sample(initial, 2)
                candidate.insert(j, candidate.pop(i))
            current_cost = observe(candidate)
            current = candidate
        else:
            i, j = rng.sample(initial, 2)
            candidate.insert(j, candidate.pop(i))
            cost = observe(candidate)
            if cost <= current_cost:
                current_cost = cost
                current = candidate
        steps += 1
    return dict(neh=neh, steps=steps, elapsed=time.perf_counter() - started,
                cpu=time.process_time() - cpu_start, improvements=history)


def select_cases(directory, config):
    for filename in FILES:
        path = directory / filename
        instances = config["load_data"](str(path))
        dev = config["get_dev"]()[filename]
        for index in sorted(set(range(len(instances))) - set(dev))[:2]:
            yield filename, index, instances[index]


def verify(record, directory, config):
    expected_hashes = {name: sha256(directory / name) for name in (*FILES, "config.py")}
    assert record["input_sha256"] == expected_hashes, "Changed config or input"
    expected = list(select_cases(directory, config))
    assert len(record["runs"]) == len(expected) == 6
    summary = []
    for row, (filename, index, case) in zip(record["runs"], expected):
        assert (filename, index) == (row["file"], row["index"])
        previous_time, previous_cost = -1, float("inf")
        for event in row["improvements"]:
            answer = event["permutation"]
            assert sorted(answer) == list(range(1, case["n"] + 1))
            assert previous_time <= event["elapsed"] and previous_cost > event["makespan"]
            score = config["eval_func"](**case, job_sequence=answer)
            assert abs(score - case["lower_bound"] / event["makespan"]) < 1e-12
            previous_time, previous_cost = event["elapsed"], event["makespan"]
        checkpoints = []
        for limit in BUDGETS:
            available = [e for e in row["improvements"] if e["elapsed"] <= limit]
            checkpoints.append(available[-1]["makespan"] if available else None)
        summary.append([filename, index, case["lower_bound"], row["neh"]["makespan"], *checkpoints])
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="directory containing Flow shop scheduling/config.py and inputs")
    parser.add_argument("results", type=Path, help="result JSON to write or verify")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    config = runpy.run_path(str(args.data / "config.py"))
    if args.verify:
        record = json.loads(args.results.read_text())
    else:
        import psutil
        process = psutil.Process()
        core = process.cpu_affinity()[0]
        process.cpu_affinity([core])
        record = dict(platform=platform.platform(), python=platform.python_version(),
                      processor=platform.processor(), logical_cpu=core, available_cpus=os.cpu_count(),
                      psutil=psutil.__version__, seed=0, budgets=list(BUDGETS),
                      input_sha256={f: sha256(args.data / f) for f in (*FILES, "config.py")}, runs=[])
        for filename, index, case in select_cases(args.data, config):
            trial = search(case["matrix"])
            record["runs"].append(dict(file=filename, index=index, **trial))
        verify(record, args.data, config)
        args.results.parent.mkdir(parents=True, exist_ok=True)
        with args.results.open("x", encoding="utf-8") as file:
            json.dump(record, file, indent=1)
            file.write("\n")
    print("file, index, lower bound, NEH, 1s, 10s, 30s")
    for row in verify(record, args.data, config):
        print(*row, sep=", ")


if __name__ == "__main__":
    main()
