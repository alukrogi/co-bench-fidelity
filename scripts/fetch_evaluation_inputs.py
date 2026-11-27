"""Fetch the public files used by check_evaluation.py and budget_pilot.py."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


REVISION = "6e561a36254d4315b8c2d155e81a465b634e87e1"
APRIL = "585d2412ced2dfd2e265606d845f67eed589bdff"
AUGUST = "55493594b9f2235641f577ef9e478e5f9b7e3315"
REPO = "CO-Bench/CO-Bench"
RAW_TASKS = {
    "Assignment problem", "Constrained guillotine cutting", "Flow shop scheduling",
    "Job shop scheduling", "Open shop scheduling", "Packing unequal circles",
    "Packing unequal circles area", "Packing unequal rectangles and squares",
    "Packing unequal rectangles and squares area", "Travelling salesman problem",
}
COVER_FILES = {"scp41.txt", "scpb1.txt", "scpc1.txt", "scpe1.txt"}


def fetch(url):
    with urlopen(url, timeout=90) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    target = parser.parse_args().destination
    target.mkdir(parents=True, exist_ok=True)

    def download(item, revision, path):
        body = fetch(f"https://huggingface.co/datasets/{REPO}/resolve/{revision}/"
                     + quote(item["path"]))
        if "lfs" in item:
            matches = hashlib.sha256(body).hexdigest() == item["lfs"]["oid"]
        else:
            header = f"blob {len(body)}\0".encode()
            matches = hashlib.sha1(header + body).hexdigest() == item["oid"]
        if not matches:
            raise ValueError(f"Object hash mismatch for {item['path']}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    with ThreadPoolExecutor(max_workers=8) as pool:
        work = []
        for revision in (APRIL, AUGUST, REVISION):
            url = f"https://huggingface.co/api/datasets/{REPO}/tree/{revision}?recursive=true&limit=1000"
            entries = json.loads(fetch(url))
            if len(entries) >= 1000:
                raise ValueError("Pinned inventory exceeds one page")
            files = [item for item in entries if item["type"] == "file"]
            inventory = {item["path"]: item["oid"] for item in files}
            (target / f"tree-{revision}.json").write_text(json.dumps(inventory), encoding="utf-8")
            for item in files:
                name = item["path"]
                if "/" not in name:
                    continue
                task, filename = name.split("/", 1)
                if revision == REVISION:
                    if not (filename == "config.py" or
                            (filename.endswith(".txt") and task in RAW_TASKS) or
                            (task == "Set covering" and filename in COVER_FILES)):
                        continue
                    # The vehicle-routing directory contains a colon on the upstream POSIX tree.
                    path = target / task.replace(":", "_") / filename
                elif revision == APRIL and filename == "config.py" and task in {
                        "Assignment problem", "Packing unequal circles area"}:
                    path = target / "april" / task / "config.py"
                else:
                    continue
                work.append(pool.submit(download, item, revision, path))
        for result in work:
            result.result()
    print(f"Verified {len(work)} files and saved three dated inventories in {target}")


if __name__ == "__main__":
    main()
