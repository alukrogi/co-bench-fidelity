"""Reconcile CO-Bench Appendix A with Figure 3 and examine fixed-suite sensitivity."""

import argparse
import csv
from decimal import Decimal
from pathlib import Path
from statistics import mean, median

METHODS = ("Classical Solver", "BestOfN", "Refine", "FunSearch", "AIDE", "ReEvo", "MCTS", "EoH")
# Transcribed from the published AAAI Figure 3, p. 33130.
HEADLINE = ("0.797", "0.774", "0.840", "0.842", "0.753", "0.774", "0.762", "0.840")
ABOVE = ("", "0.417", "0.694", "0.639", "0.278", "0.444", "0.444", "0.555")
# Appendix labels of the six tasks flagged by check_evaluation.py at the current data pin.
OVERLAP = {"Constrained guillotine cutting", "Packing unequal circles", "Packing unequal circles area",
           "Packing unequal rectangles and squares", "Packing unequal rectangles and squares area", "TSP"}


def extract(html):
    from bs4 import BeautifulSoup
    article = BeautifulSoup(html.read_bytes(), "html.parser")
    rows = []
    for number in range(3, 39):
        table_id = f"A1.T{number}"
        figure = article.find("figure", id=table_id)
        task = figure.figcaption.get_text(" ", strip=True).split(": ", 1)[1]
        pairs = [tuple(cell.get_text(strip=True) for cell in row.select("td, th"))
                 for row in figure.select("tbody tr")]
        assert len(pairs) == len(METHODS) and set(dict(pairs)) == set(METHODS)
        rows.append(dict(table=table_id, task=task, **dict(pairs)))
    assert len({r["task"] for r in rows}) == 36
    return rows


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def calculate(rows):
    assert len(rows) == 36 and len({row["table"] for row in rows}) == 36
    summaries = []
    by_method = {m: [Decimal(r[m]) for r in rows] for m in METHODS}
    remaining = [row for row in rows if row["task"] not in OVERLAP]
    assert len(remaining) == 30
    classical = by_method["Classical Solver"]
    for method, headline, above in zip(METHODS, HEADLINE, ABOVE):
        scores = by_method[method]
        delta = [x - y for x, y in zip(scores, classical)]
        summaries.append(dict(method=method, figure3_mean=headline, appendix_mean=f"{mean(scores):.9f}",
                              mean_excluding_six_shared_split_tasks=f"{mean(Decimal(r[method]) for r in remaining):.9f}",
                              figure3_above_classical=above,
                              strict_wins=sum(d > 0 for d in delta), exact_ties=delta.count(0),
                              strict_losses=sum(d < 0 for d in delta),
                              wins_margin_gt_1e_9=sum(d > Decimal("1e-9") for d in delta)))
    pairs = []
    for other in ("Refine", "EoH", "Classical Solver", "ReEvo"):
        delta = [x - y for x, y in zip(by_method["FunSearch"], by_method[other])]
        for r, d in zip(rows, delta):
            pairs.append(dict(method="FunSearch", comparator=other, omitted_task=r["task"],
                              difference_on_task=str(d), full_mean_difference=f"{mean(delta):.9f}",
                              median_task_difference=f"{median(delta):.9f}",
                              remaining_mean_difference=f"{(sum(delta)-d)/(len(delta)-1):.9f}"))
    return summaries, pairs


def plot(rows, path):
    import matplotlib.pyplot as plt
    labels = {"Refine": "Greedy Refinement", "Classical Solver": "Classical baseline"}
    rows = sorted(rows, key=lambda r: Decimal(r["FunSearch"]) - Decimal(r["Refine"]))
    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(10, 10.6))
    for ax, (key, title) in zip(axes, labels.items()):
        differences = [float(Decimal(r["FunSearch"]) - Decimal(r[key])) for r in rows]
        ax.axvline(0, color="0.62", linewidth=0.8)
        ax.hlines(range(len(rows)), 0, differences, color="0.76", linewidth=1)
        ax.scatter(differences, range(len(rows)), s=16,
                   c=["#9a482d" if d < 0 else "#206c77" for d in differences], zorder=3)
        ax.set_title(f"FunSearch minus {title}", fontsize=11, loc="left")
        ax.set_xlim(-0.45, 0.45)
        ax.set_xticks([-.4, -.2, 0, .2, .4])
        ax.set_xlabel("Difference in task score")
        ax.grid(axis="x", alpha=.13)
        ax.tick_params(length=0, labelsize=8, pad=4)
        ax.spines[["top", "left", "right"]].set_visible(False)
    axes[0].set_yticks(range(len(rows)), [r["task"] for r in rows])
    fig.subplots_adjust(left=.34, right=.985, bottom=.075, top=.955, wspace=.12)
    fig.savefig(path, dpi=165, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, help="optionally re-extract from the v3 HTML")
    parser.add_argument("--evidence", type=Path, default=Path("evidence"))
    parser.add_argument("--plot", action="store_true", help="also render the paired task differences")
    args = parser.parse_args()
    appendix = args.evidence / "appendix-scores.csv"
    if args.html:
        write_rows(appendix, extract(args.html))
    with appendix.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    summaries, pairs = calculate(rows)
    write_rows(args.evidence / "figure3-reconciliation.csv", summaries)
    write_rows(args.evidence / "leave-one-task-out.csv", pairs)
    if args.plot:
        plot(rows, args.evidence / "task-differences.png")
    for r in summaries:
        print(r["method"], r["figure3_mean"], r["appendix_mean"], r["strict_wins"], r["exact_ties"])


if __name__ == "__main__":
    main()
