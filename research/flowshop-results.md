# What changed after ten seconds on six flow-shop instances?

A fixed local search produced a better schedule after ten seconds on four of the six cases. The other two kept the same best makespan through 30 seconds. On the largest pair, the 10-to-30-second gains were 15 and 42 makespan units. This is a paired measurement on one family. It demonstrates how to measure the deployment-budget effect without changing the model, program, input or seed. [Design committed before execution](flowshop-design.md) · [Search and witness checker](../scripts/flowshop_budget.py) · [All timed improvements and permutations](../evidence/flowshop-traces.json)

| Released file | Index | File lower bound | NEH construction | 1 s | 10 s | 30 s |
|---|---:|---:|---:|---:|---:|---:|
| tai20_5 | 1 | 1,290 | 1,365 | 1,360 | 1,359 | 1,359 |
| tai20_5 | 2 | 1,073 | 1,159 | 1,087 | 1,087 | 1,087 |
| tai50_10 | 0 | 2,907 | 3,135 | 3,112 | 3,091 | 3,059 |
| tai50_10 | 1 | 2,821 | 3,032 | 2,995 | 2,935 | 2,929 |
| tai100_20 | 3 | 6,072 | 6,557 | 6,542 | 6,520 | 6,505 |
| tai100_20 | 4 | 6,009 | 6,695 | 6,695 | 6,668 | 6,626 |

Lower makespan is better. Indices are zero-based. The first two test indices in each size file were fixed in the design. Every timed column comes from the same continuing search on that instance. Each incumbent is a full job permutation. Each one passed the public evaluator's feasibility check and its separate makespan recurrence. The lower bound was used by the verifier after execution and was withheld from the search. Equality to a loose lower bound is unnecessary for a schedule to be feasible or to improve.

The worker was pinned to one logical CPU on Windows 11 with CPython 3.12.7. Input loading, interpreter startup and post-run checks were outside the clock. Runs used 29.91–30.00 process CPU seconds across 30 wall seconds apiece. The first feasible input-order permutation was available before the NEH insertion procedure finished. Each checkpoint credits the most recent *completed* improving answer at or before that time. The measurement represents an anytime deployment policy. It neither implies that the historical finalists could yield incumbents nor establishes a rank reversal for agents. The independent set-covering pilot complements it: in two cases added time bought an optimality certificate after the incumbent already matched the reference. [Evaluator and pilots](evaluation.md) · [Data and task contract](https://huggingface.co/datasets/CO-Bench/CO-Bench/tree/6e561a36254d4315b8c2d155e81a465b634e87e1/Flow%20shop%20scheduling)

After fetching the inputs as described in the README, the recorded witness checks run without a timer. A fresh timing run writes a new file and can vary with hardware and scheduling.

```sh
python -B scripts/flowshop_budget.py ".sources/eval-replay/Flow shop scheduling" evidence/flowshop-traces.json --verify
python -B scripts/flowshop_budget.py ".sources/eval-replay/Flow shop scheduling" work/new-flowshop.json
```
