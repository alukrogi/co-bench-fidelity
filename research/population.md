# How many instances does the public benchmark score?

Table 1 labels 6,482 as the number of test-set instances. The current public release yields **3,505 test records** when the task loaders and split filters run across all 36 tasks. It contains **6,461 records in total**, including development, and six tasks select the same 301 records for both splits. The distinction matters for replication: 2,977 separates the quoted number from the test count, while 21 separates it from the entire loaded population. A manifest identifying the instances behind Table 1 would resolve which population the authors counted. [AAAI Table 1 and caption](https://ojs.aaai.org/index.php/AAAI/article/download/40596/44557) · [Machine-readable census](population.json)

## Data and independent verification

We used the public Hugging Face file tree at `6e561a3` and the GitHub evaluator at `2f6620b`. We compared the 856 names and Git object IDs in the public tree with the previous private audit’s inventory. All matched. To avoid a redundant download, we used its local data cache as a byte source. We independently verified all 854 task files against public object IDs, including 249 Git LFS objects checked by reconstructing their pointers from file size and SHA-256. The remaining two root files are the dataset card and Git attributes. We reran all 36 tasks’ public loaders, checked normalization preserved group lengths, and executed the upstream development and test filters on positional identifiers. The prior audit’s counts and case manifest were excluded from the calculation. All 36 per-task counts for loaded records, development, test, overlap and test groups then matched its figures. [Public dataset revision](https://huggingface.co/datasets/CO-Bench/CO-Bench/tree/6e561a36254d4315b8c2d155e81a465b634e87e1) · [Census program](../scripts/count_population.py) · [Evaluator order](https://github.com/sunnweiwei/CO-Bench/blob/2f6620ba5cc8d80d6fefc121b5ee2c4dcec29f33/evaluation/evaluate.py#L54-L68) · [Split functions](https://github.com/sunnweiwei/CO-Bench/blob/2f6620ba5cc8d80d6fefc121b5ee2c4dcec29f33/evaluation/utils.py#L330-L366)

An instance here is one positional record returned by a loader within a task and score group. Multiple records can share a physical file, and different tasks may use identical geometry. A test group is one top-level input entry with at least one normalized score surviving the test filter. The pinned release contains 576 scored groups overall and 407 test groups spanning 544 physical test inputs. Membership satisfies 3,257 development + 3,505 test − 301 shared = 6,461 loaded records. [Group discovery](https://github.com/sunnweiwei/CO-Bench/blob/2f6620ba5cc8d80d6fefc121b5ee2c4dcec29f33/evaluation/utils.py#L73-L77) · [Input-level counts](population.json)

MIS illustrates the weights behind those units. Its top-level entries are graph directories. We loaded each graph separately using the task’s own single-file loader to limit peak memory. The directory loader also processes one graph per file. It finds 128 small test graphs, 16 large graphs, and 100 validation graphs. The split assigns five of the large graphs and all 100 validation graphs to development. The group mean assigns one half of the MIS score to 128 small graphs and one half to 11 large graphs. A single large graph consequently has about 11.6 times the weight of a small graph in this task score. The directory traversal has no explicit sort, and the five development indices for large graphs are positional. Counts are stable under reordering, while the identities at those positions require the enumeration order. The extra `.DS_Store` entry fails the loader and the MIS normalizer discards its key. [MIS loader](https://huggingface.co/datasets/CO-Bench/CO-Bench/blob/6e561a36254d4315b8c2d155e81a465b634e87e1/Maximal%20independent%20set/config.py#L28-L94) · [MIS normalizer and split](https://huggingface.co/datasets/CO-Bench/CO-Bench/blob/6e561a36254d4315b8c2d155e81a465b634e87e1/Maximal%20independent%20set/config.py#L144-L172) · [Released group averaging](https://github.com/sunnweiwei/CO-Bench/blob/2f6620ba5cc8d80d6fefc121b5ee2c4dcec29f33/evaluation/utils.py#L369-L375)

## Version effects

| Public data revision | Loaded in union | Development | Test | In both | Evidence |
|---|---:|---:|---:|---:|---|
| April snapshot `585d241` | 6,361 | 3,157 | 3,501 | 297 | Reconstructed by inventory and split differences. Its four circle-area instances are all development-only. |
| August snapshot `5549359` | 6,361 | 3,157 | 3,505 | 301 | Reconstructed by inventory and split differences. Removing the circle-area development map put all four in both splits. |
| Current pin `6e561a3` | 6,461 | 3,257 | 3,505 | 301 | Recounted from all 854 verified task files. |

Only the circle-area config and dataset card change between the April and August trees. Between August and the current pin the release adds 100 MIS validation graphs and a root Git attributes file, and changes the card and the direction of assignment score normalization. The assignment correction leaves positional membership unchanged. The author publicly confirmed that the MIS validation split had been missing from the release. Restoring it increases the development population by 100 and changes the test count by zero. The first public GitHub split functions also use the same membership rules. These observed changes explain the differences between the three public populations. They provide no identified set of 6,482 test cases. [April tree](https://huggingface.co/datasets/CO-Bench/CO-Bench/tree/585d2412ced2dfd2e265606d845f67eed589bdff) · [August tree](https://huggingface.co/datasets/CO-Bench/CO-Bench/tree/55493594b9f2235641f577ef9e478e5f9b7e3315) · [Earlier GitHub evaluator](https://github.com/sunnweiwei/CO-Bench/blob/93d91b5cf86987d514fe40519245bdf6d11aea70/evaluation/utils.py) · [Historical checks](evaluation-checks.json) · [Author confirmation and repair](https://github.com/sunnweiwei/CO-Bench/issues/5#issuecomment-3736955147)

## Per-task census at the current pin

| Dataset directory | Loaded | Development | Test | In both | Test groups |
|---|---:|---:|---:|---:|---:|
| Aircraft landing | 49 | 20 | 29 | 0 | 13 |
| Assignment problem | 12 | 4 | 8 | 0 | 8 |
| Assortment problem | 12 | 4 | 8 | 0 | 8 |
| Bin packing - one-dimensional | 160 | 40 | 120 | 0 | 8 |
| Capacitated warehouse location | 49 | 12 | 37 | 0 | 37 |
| Common due date scheduling | 70 | 21 | 49 | 0 | 7 |
| Constrained guillotine cutting | 3 | 3 | 3 | 3 | 3 |
| Constrained non-guillotine cutting | 651 | 320 | 331 | 0 | 4 |
| Container loading | 762 | 380 | 382 | 0 | 9 |
| Container loading with weight restrictions | 700 | 350 | 350 | 0 | 7 |
| Corporate structuring | 10 | 5 | 5 | 0 | 5 |
| Crew scheduling | 49 | 20 | 29 | 0 | 10 |
| Equitable partitioning problem | 10 | 4 | 6 | 0 | 6 |
| Euclidean Steiner problem | 242 | 114 | 128 | 0 | 15 |
| Flow shop scheduling | 120 | 60 | 60 | 0 | 12 |
| Generalised assignment problem | 84 | 36 | 48 | 0 | 16 |
| Graph colouring | 30 | 15 | 15 | 0 | 15 |
| Hybrid Reentrant Shop Scheduling | 1,350 | 675 | 675 | 0 | 27 |
| Job shop scheduling | 80 | 40 | 40 | 0 | 8 |
| Maximal independent set | 244 | 105 | 139 | 0 | 2 |
| Multi-Demand Multidimensional Knapsack problem | 810 | 405 | 405 | 0 | 9 |
| Multidimensional knapsack problem | 325 | 162 | 163 | 0 | 11 |
| Open shop scheduling | 60 | 30 | 30 | 0 | 6 |
| Packing unequal circles | 4 | 4 | 4 | 4 | 4 |
| Packing unequal circles area | 4 | 4 | 4 | 4 | 4 |
| Packing unequal rectangles and squares | 9 | 9 | 9 | 9 | 6 |
| Packing unequal rectangles and squares area | 9 | 9 | 9 | 9 | 6 |
| Resource constrained shortest path | 24 | 12 | 12 | 0 | 12 |
| Set covering | 87 | 38 | 49 | 0 | 49 |
| Set partitioning | 59 | 29 | 30 | 0 | 30 |
| Travelling salesman problem | 272 | 272 | 272 | 272 | 3 |
| Uncapacitated warehouse location | 15 | 7 | 8 | 0 | 8 |
| Unconstrained guillotine cutting | 26 | 13 | 13 | 0 | 13 |
| Vehicle routing: period routing | 10 | 5 | 5 | 0 | 5 |
| p-median - capacitated | 20 | 10 | 10 | 0 | 1 |
| p-median - uncapacitated | 40 | 20 | 20 | 0 | 20 |
| **Total** | **6,461** | **3,257** | **3,505** | **301** | **407** |

## Reproduction

The census accepts a complete materialized public dataset and a pinned CO-Bench checkout. The script recognizes both upstream directory names and sanitized directory names. It verifies all task files before loading them. Tested with Python 3.12.7, NumPy 1.26.4 and NetworkX 3.1. On a POSIX host with Git LFS, obtain the full dataset and run:

```sh
git clone https://huggingface.co/datasets/CO-Bench/CO-Bench .sources/full-dataset
git -C .sources/full-dataset checkout 6e561a36254d4315b8c2d155e81a465b634e87e1
git -C .sources/full-dataset lfs pull
git clone https://github.com/sunnweiwei/CO-Bench .sources/CO-Bench
git -C .sources/CO-Bench checkout 2f6620ba5cc8d80d6fefc121b5ee2c4dcec29f33
python -m pip install numpy==1.26.4 networkx==3.1
python -B scripts/count_population.py .sources/full-dataset .sources/CO-Bench
```

For offline use, pass `--inventory path/to/tree-6e561a36254d4315b8c2d155e81a465b634e87e1.json` from the evaluation input fetcher. The script checks the inventory’s canonical hash in either mode. [Input fetcher](../scripts/fetch_evaluation_inputs.py)
