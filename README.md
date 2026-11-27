# How faithfully does CO-Bench evaluate algorithm-search methods?

**CO-Bench provides useful evidence that LLM search can produce competitive short-budget solvers. Its published rankings give substantially weaker evidence about the relative merit of the original FunSearch, EoH, ReEvo and MCTS-AHD frameworks.** Some adaptations preserve the central search rule. Others change the information passed between generations, the parents selected, the operators executed, or the compute required per candidate. There are also discrepancies between the published scores, stated test population and public evaluation path.

The authors explicitly describe adapting the frameworks to generate complete solvers, an important and legitimate benchmark design choice. This audit asks which mechanisms survived that choice, whether the released protocol implements the written one, and which numerical conclusions can be reproduced. It covers the AAAI paper, all three arXiv versions, the 36 appendix tables, public code and data history, maintainer replies, original framework papers, supplementary methods and code, and the private lace-audit study. Evidence reviewed 27 November 2026. [Published article](https://doi.org/10.1609/aaai.v40i39.40596) · [Extended appendix](https://arxiv.org/html/2504.04310v3#A1) · [Source history and prior audit](research/provenance.md)

## What the evidence establishes

| Question | Finding |
|---|---|
| Does the headline reproduce? | FunSearch's 36 scores average **0.842286**, Greedy Refinement's **0.840106**, and classical's **0.797275**. EoH's average is **0.800679** against **0.840** in Figure 3. The public artifacts do not settle which EoH result represents the intended runs. [Reconciliation](research/published-results.md) |
| How robust is the ordering? | FunSearch's lead over classical survives all 36 single-task omissions. Its lead over Greedy Refinement reverses if any one of three tasks is omitted. For FunSearch, 21 task wins and two ties give 23/36, the displayed “Above Classical” value when ties count. The paper alternates between problems and instances as the denominator. [Paired results and figure](research/published-results.md) |
| Are the public test cases held out? | We verified every one of the 854 task files against the pinned public inventory and ran the loaders and selectors. They yield **6,461 cases**, **3,257 development**, **3,505 test**, and **301 shared across six tasks**. The paper calls **6,482** its test count. The released TSP inputs also include reference-quality tours for 256 cases. Use by historical agents remains unestablished. [Full census](research/population.md) · [Interface and split checks](research/evaluation.md) |
| Do the scores mean the same thing on every task? | Equation (6) bounds scores by one. Fourteen appendix cells exceed 1.000001, the largest reaching **1.083901**. The released code averages within file groups first. In TSP its 16 largest cases carry one third of the task weight; under equal-case weighting they would carry 5.88%. A change of scoring rule can even reverse the reward for shortening a real tour. [Scoring audit](research/evaluation.md) · [Tour rescoring](research/provenance.md) |
| Did ten seconds make exact solving impossible on most instances? | The cited materials do not provide a suite-wide exact-solver census, proof logs or calibration establishing that assertion. The maintainer explicitly confirmed that ten minutes had not been tested on CO-Bench. Our independent exact controls and flow-shop trials show that extra seconds can improve an incumbent, buy a certificate, or leave the answer unchanged. Their samples do not determine what fraction of the full suite is solvable. [Maintainer reply](https://github.com/sunnweiwei/CO-Bench/issues/7#issuecomment-3875276329) · [Exact controls](research/evaluation.md) · [1/10/30-second schedules](research/flowshop-results.md) |
| Is the classical or neural comparison decisive? | The classical baseline reflects about 30 minutes per task for selecting and tuning a solver. A full historical portfolio with run settings and outputs could not be located. In Table 2, using DIMES's published MCTS decoder instead of its displayed sampling result reverses the TSP-1000 comparison with both CO-Bench agents. The source studies also used different devices and parallelism. [Classical setup](research/evaluation.md) · [Neural comparison](research/neural-comparison.md) |

## Which framework ideas survived?

| Released method | Mechanism-level assessment |
|---|---|
| **EoH** | Keeps population search, rank-weighted parent draws and several original operators. It asks for prose and code, then stores the extracted code in both fields and passes parent code alone to the next prompts. This removes EoH's separate inherited thought representation. Its default minimization also requires an explicit override or score transformation. [Original and adapted paths, offline trace](research/eoh-reevo.md#eoh) |
| **FunSearch** | Keeps islands, examples and periodic resets. Its database groups by a scalar score and takes exemplars from the highest-scoring clusters. Upstream uses per-input performance signatures and probabilistic cluster sampling. Distinct behaviors with identical means can lose representation. [Comparison and probe](research/funsearch-and-controls.md#funsearch) |
| **ReEvo** | Implements short and long reflection, crossover and elite mutation. It changes their order and frequency, and hard-codes a second model for short reflection. Two 64-candidate mock traces took **61 and 721 requests** depending on the score sequence. These are demonstrations of the released code, not estimates of historical spend. [Comparison and traces](research/eoh-reevo.md#reevo) |
| **MCTS-AHD** | Keeps a tree, UCT and widening. The default leaf-action loop returns at its first enabled action and restarts traversal on the next step. Mutation and tree-path synthesis drop out. A 64-candidate fixture reached none of the three affected operators. [Schedule and trace](research/funsearch-and-controls.md#mcts-ahd) |
| **AIDE and Chain-of-Experts** | AIDE retains drafting, debugging and improvement but uses a second model to interpret intermediate feedback. Chain-of-Experts preserves the expert collaboration loop and returns one externally scored candidate. Its internal consultations and trials constitute a different resource budget. [AIDE](research/funsearch-and-controls.md#aide) · [Chain-of-Experts](research/funsearch-and-controls.md#chain-of-experts) |
| **Direct Answer, BestOfN and Greedy Refinement** | Follow their stated roles closely: a single solver, repeated independent proposals selected on development, and iterative revision of the best observed program. These controls are essential for judging the added value of population search. [Controls](research/funsearch-and-controls.md#direct-answer-bestofn-and-greedy-refinement) |

The historical launcher, selected candidate hashes, solver settings and per-instance outputs behind Figure 3 remain the main missing evidence. The maintainer's account that Assignment stopped after the first round gives one documented exception to the paper's general 64-candidate description. Differences in public source establish what a reproducer runs today. Ranking the original frameworks across budgets requires paired experiments or recovery of the original runs. [Release chronology](research/provenance.md) · [Historical artifact request and replication protocol](research/replication-protocol.md)

## Reproduce the checks

The table arithmetic runs offline with the Python standard library. The checked-in CSV contains the appendix's published decimals. To rebuild that CSV from the versioned article and regenerate the figure, use Python with Beautiful Soup and Matplotlib.

```sh
python -B scripts/appendix.py
python -m pip install beautifulsoup4 matplotlib
curl -fL --create-dirs https://arxiv.org/html/2504.04310v3 -o .sources/paper-v3.html
python -B scripts/appendix.py --html .sources/paper-v3.html --plot
```

For framework probes and the focused evaluator checks, start with the following from the repository root in an isolated Python 3.12 environment. The probes use scripted model responses. No API credentials are required. The fetcher downloads published inputs at specified revisions and checks their object hashes. The timing runs require a host supporting process CPU affinity.

```sh
git clone https://github.com/sunnweiwei/CO-Bench.git .sources/CO-Bench
git -C .sources/CO-Bench checkout 2f6620ba5cc8d80d6fefc121b5ee2c4dcec29f33
python -m pip install numpy==1.26.4 scipy==1.13.1 psutil==5.9.0 requests==2.32.3 omegaconf==2.3.0 tqdm networkx==3.1
python -B scripts/trace_evolution.py .sources/CO-Bench
python -B scripts/probe_frameworks.py .sources/CO-Bench
python -B scripts/fetch_evaluation_inputs.py .sources/eval-replay
python -B -W ignore::SyntaxWarning scripts/check_evaluation.py .sources/eval-replay .sources/CO-Bench
python -B scripts/flowshop_budget.py ".sources/eval-replay/Flow shop scheduling" evidence/flowshop-traces.json --verify
python -B scripts/budget_pilot.py .sources/eval-replay
```

The [full population census](research/population.md#reproduction) uses the complete public dataset. The [flow-shop design](research/flowshop-design.md) and [witnesses](evidence/flowshop-traces.json) preserve what was timed. The [replication protocol](research/replication-protocol.md) specifies how to test the remaining causal questions with frozen programs, disjoint cases, repeated searches, common budgets and independently validated solutions.
