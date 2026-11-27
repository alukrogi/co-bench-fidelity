# What would settle the remaining questions?

Three experiments answer different questions. Replaying a historical finalist establishes what that program can do under a new deadline. Regenerating a search under matched conditions measures a method. Testing exact solvers with bounds measures how difficult the instances are for a specified solver portfolio. Each experiment should keep its own denominator and decision rule.

## 1. Recover the historical comparison

The smallest useful author release links each Figure 3 row to its 36 task results, and each task result to a program, a split and an evaluator. Ask for the following bundle. A saved hash plus a retrievable archive suffices for large objects.

| Record | What it resolves |
|---|---|
| Experiment commit, driver command, working-tree changes, OS/image, packages, CPU affinity, solver versions and licenses | Which wrapper ran, which native calls were available, whether the stated limits were enforced |
| Task, file digest, within-file index, dev/test flag, weight, reference value and evidence for the reference | Held-out membership, instance count, file weighting, optimality and use of bounds |
| Search seed, per-role model snapshot, prompts, parent IDs, sampled responses, parse/repair outcomes, token usage and timestamps | Inherited descriptions, diversity, reflection, active operators, actual calls and compute |
| Candidate source/hash, per-instance development outcomes, tie/early-stop rule, final selection hash | Which program won and why, including the reported assignment exception |
| Test calls for that finalist and the classical comparator, validated witnesses, raw objective, status, elapsed time, best bound when available | Strict wins, ties, actual failures, exactness and uncertainty |
| Figure-generation code, baseline tuning records, version-to-version change log | EoH's two totals, the unit of “Above Classical,” variant selection and the provenance of the published classical control |

First regenerate the released aggregates from these frozen records. Then rerun the finalists on the *original* configuration. Report any difference at the first stage where it appears (selection, membership, objective, normalization, aggregation or plotting). Preserve both values when a discrepancy remains. No new model sampling is needed for either calculation if the programs are available.

## 2. Compare deployment budgets

Freeze one winning program per method, task and discovery seed and freeze the classical formulations and parameters. Record if a program embeds a literal ten-second stopping rule. Keep unchanged-program replay and a separate runs-with-retuned-limit condition. Giving a program a longer external deadline cannot help it use that time if it exits early. A third, more expensive condition should rerun discovery with the target budget included in every method's prompt and evaluator.

- Use the same cases and hardware for every method. Start with 1, 3, 10, 30, 60 and 600 seconds. Keep 10 seconds as the reference condition and 600 seconds as the directly raised alternative. Stratify by task and instance size. Rotate run order, record background load and calibrate the CPU; cap native threads and descendants. Define when loading, model construction, compilation, warm-up, validation and answer delivery are charged.
- Run the paper's **single return under a hard wall deadline** as the primary replay. In a separate experiment instrument publication of feasible incumbents, record the time each complete witness becomes available, and validate it. Missing answers at a cutoff receive the protocol's failure score. Save all timeout, infeasibility and error statuses. An incumbent recovered from a solver that otherwise times out is a different deployment service.
- For the exactness claim, distinguish feasible objective equal to a reference, feasible improvement over a best-known value, and a certified optimum. Predeclare solvers and formulations per family, primal/dual gap tolerances, solver and external wall limits, and whether presolve or a polynomial-time exact algorithm applies. Report counts over all listed cases and per family, plus cases with unknown optima. Unsolved by a chosen solver at 10 seconds gives an observed failure rate for that solver. It cannot prove impossibility.
- Record full score-versus-time curves, feasible-return rate, objective conditional on both methods being feasible, time to target, and proof rate for the exact baselines. Show separate results under the printed equation and each native evaluator. Flag opposite-sign objectives, zero references, and improvements beyond a reference explicitly. Include time-integrated gap when a meaningful monotone incumbent and comparable target exist. [Berthold's primal integral](https://www.sciencedirect.com/science/article/abs/pii/S0167637713001181) · [Dolan and Moré on performance profiles](https://arxiv.org/abs/cs/0102001)

The decision is empirical. If changing the deployment budget or the feedback protocol changes a paired method ordering, report which task, budget and programs produce the change. If the ordering persists across the grid, report its range and uncertainty. A finding in one family does not give the prevalence of reversals in the suite.

## 3. Isolate the search mechanisms

Run the published-style port and a port that restores the specific upstream mechanism within the same full-solver interface. Add an upstream-style *component-design* condition with a documented shared outer heuristic wherever that comparison makes sense. A scaffold supplies domain knowledge and changes the search space. Give every applicable method access to it and report that factor separately.

| Comparison | Factor to change in the paired runs |
|---|---|
| EoH versus its CO-Bench port | Preserve versus drop parent thought text; separately vary synchronized vs stepwise population updates. Verify maximization with a known score sequence. |
| FunSearch versus its CO-Bench port | Per-instance performance signatures versus aggregate scores; then stochastic cluster sampling versus selecting the top clusters. Record island occupancy, exemplars, time-based resets and code-length preference. |
| ReEvo versus its CO-Bench port | Restore the generation-level order of short reflection, crossover, evaluation, long reflection and elite mutation. Hold the reflector model fixed first, then vary it. Record pair failures and population changes. |
| MCTS-AHD versus its CO-Bench port | Restore continuation through the default action sequence and condition generation on the selected tree parent. Measure actual operator counts and parent inclusion. |
| AIDE and Chain-of-Experts | Validate whether AIDE's reviewer score and bug classification agree with the official feedback. Record Chain-of-Experts' consultations, refinement depth, judge and single final submission. |
| Simple controls | Match BestOfN and Greedy Refinement on generator, prompt interface, parser, feedback, shared starts where appropriate, and stopping rule. Preserve a genuine one-shot baseline. |

Use paired independent **discovery** blocks, with common model snapshots and starting draws where supported. Specify a pilot-based precision target and replication count before the main study. Randomize method order within blocks. Compare equal submitted-candidate counts first, then repeat under equal inference resources (tokens or measured monetary cost) and equal elapsed search time. Each design estimates a different quantity. Record calls, tokens, failed generations, solver executions and core-seconds in every arm.

For generalization, lock final program hashes before opening a genuinely disjoint test set. Draw extra unseen cases for release tasks with overlapping splits. Remove answer-bearing fields at the solver boundary, and keep the original interface as an explicit historical replay arm. Independently validate objectives and constraints. Use coherent ties and stable file manifests. Shared development/test labels across related tasks and model pretraining exposure remain separate questions.

Keep the paper's equal-task primary average and show paired differences for every task and search seed. Add family-stratified results and fixed-suite omission sensitivity. Cluster uncertainty at the level actually resampled; the thousands of deployment instances cannot stand in for repeated discovery runs. Publish the outcomes of every arm, including unchanged rankings, failed runs and any amendments made before testing. The limited pilots in this repository establish feasibility of parts of this design. The full factorial study has not been run.
