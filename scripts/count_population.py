"""Recount all cases from the pinned HF data using each task's own input loader."""

import argparse
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from hashlib import sha1, sha256
import io
import json
from pathlib import Path
import re
import runpy
from urllib.request import urlopen

from check_evaluation import scoring_functions
from fetch_evaluation_inputs import REVISION


INVENTORY_HASH = "99be59dcaff51b05f7ea5e5a92f3f30fe962ccf24affa9a5383e541b0bb2efb6"
UTILS_HASH = "b9eb42a878f4ff466225421bc6fd8b88135744af8fb06bee040db88d31fb9925"


def object_id(content):
    return sha1(f"blob {len(content)}\0".encode() + content).hexdigest()


def load_inventory(path):
    if path:
        inventory = json.loads(path.read_bytes())
    else:
        url = f"https://huggingface.co/api/datasets/CO-Bench/CO-Bench/tree/{REVISION}?recursive=true&limit=1000"
        with urlopen(url, timeout=90) as response:
            inventory = {x["path"]: x["oid"] for x in json.load(response) if x["type"] == "file"}
    canonical = json.dumps(inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    if sha256(canonical).hexdigest() != INVENTORY_HASH:
        raise ValueError("Pinned public inventory differs")
    return inventory


def verify_file(path, expected):
    content = path.read_bytes()
    if object_id(content) == expected:
        return "git"
    pointer = (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{sha256(content).hexdigest()}\nsize {len(content)}\n"
    ).encode()
    if object_id(pointer) != expected:
        raise ValueError(f"Data differ from pinned object at {path}")
    return "lfs"


def enumerate_task(task, folder, files, scoring):
    verified = Counter()
    for name, oid in files.items():
        verified[verify_file(folder / name, oid)] += 1
    config = runpy.run_path(str(folder / "config.py"))
    dev_map = config.get("get_dev", lambda: None)()
    groups = defaultdict(list)
    for name in sorted(files):
        if not name.endswith(".py"):
            groups[name.split("/", 1)[0]].append(name)

    scores = {}
    rejected = []
    sizes = {}
    with redirect_stdout(io.StringIO()):
        for group, members in groups.items():
            path = folder / group
            if group == ".DS_Store":
                # This metadata file fails the loader, and the MIS normalizer drops it.
                try:
                    config["load_data"](str(path))
                except Exception as error:
                    assert group not in config["norm_score"]({group: (None, str(error))})
                    rejected.append(group)
                    continue
                raise ValueError("Unexpectedly accepted a metadata file")
            if path.is_dir():
                # The MIS directory loader calls its single-file reader once per graph.
                # Load the same members individually to keep peak memory below one group.
                assert all(name.endswith(".gpickle") for name in members)
                for name in members:
                    assert len(config["load_data"](str(folder / name))) == 1
                size = len(members)
            else:
                size = len(config["load_data"](str(path)))
            sizes[group] = size
            scores[group] = ([1.0] * size, None)
        normalized = config.get("norm_score", lambda x: x)(scores)
    if {key: len(vals) for key, (vals, _) in normalized.items()} != sizes:
        raise ValueError(f"Normalization changed group lengths for {task}")
    indices = {key: (list(range(size)), None) for key, size in sizes.items()}
    dev = scoring["filter_dev"](indices, dev_map)
    test = scoring["filter_test"](indices, dev_map)
    membership = lambda split: {(key, ix) for key, (vals, _) in split.items() for ix in vals}
    dev_ids, test_ids = membership(dev), membership(test)
    assert len(dev_ids | test_ids) == sum(sizes.values())
    summary = dict(
        cases=sum(sizes.values()), dev=len(dev_ids), test=len(test_ids), overlap=len(dev_ids & test_ids),
        groups=len(sizes), test_groups=len(test),
        test_input_files=sum(len(test[g][0]) if len(groups[g]) > 1 else 1 for g in test),
    )
    return summary, verified, rejected, {
        group: {"all": total, "dev": len(dev.get(group, ([],))[0]), "test": len(test.get(group, ([],))[0])}
        for group, total in sizes.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="HF dataset folder containing the 36 task directories")
    parser.add_argument("repo", type=Path, help="Pinned CO-Bench code checkout")
    parser.add_argument("--inventory", type=Path, help="Optional offline path-to-blob-ID mapping from fetch_evaluation_inputs.py")
    args = parser.parse_args()
    inventory = load_inventory(args.inventory)
    source = (args.repo / "evaluation/utils.py").read_bytes().replace(b"\r\n", b"\n")
    if sha256(source).hexdigest() != UTILS_HASH:
        raise ValueError("Evaluator source differs from the pinned version")
    scoring = scoring_functions(args.repo)
    by_task = defaultdict(dict)
    for path, oid in inventory.items():
        if "/" in path:
            task, filename = path.split("/", 1)
            by_task[task][filename] = oid
    tasks, ignored = {}, []
    totals, verified = Counter(), Counter()
    mis = None
    for task, files in sorted(by_task.items()):
        folder = args.data / task
        if not folder.is_dir():
            folder = args.data / re.sub(r"[^a-z0-9]+", "_", task.lower()).strip("_")
        row, hashes, rejected, groups = enumerate_task(task, folder, files, scoring)
        tasks[task] = row
        totals.update(row)
        verified.update(hashes)
        ignored.extend(f"{task}/{name}" for name in rejected)
        if task == "Maximal independent set":
            mis = groups
    print(json.dumps({"data_revision": REVISION, "verified_task_files": verified, "excluded": ignored,
                      "totals": totals, "tasks": tasks, "mis_groups": mis}, indent=2))


if __name__ == "__main__":
    main()
