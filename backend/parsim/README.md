# Parallel offline simulation

Run from the repository root with a Python environment that has the project
dependencies installed:

```sh
./backend/parsim/elja.py -a election.json -r 1000 -S 123 -n 10 -o results.csv
```

Add `-x results.xlsx` (`--excel results.xlsx`) to also write an Excel workbook
from the same merged results. It uses the web simulator's Excel writer, with
the quality-measure blocks, electoral-system tables and saved display precision.
CSV, Excel and statistics outputs may be requested separately or together;
their paths must differ. Excel is written once by the master after merging,
not by individual workers.

Use `-v votes.csv -e systems.json -s settings.json` instead of `-a` for
separate input files. The `-r`, `-i`, `-S`, `-o`, and `-O` options have
the same meanings as in `backend/sim.py`. Here `-C` caps simulation processes
per node; by default Elja uses one process per physical core. Run `elja.py`
on Elja; it always uses Slurm. For local multicore simulations, use
`backend/sim.py`.
Elja allows at most 30 concurrent jobs for this account, and each node uses
one job. Requests with `-n` above 30 exit before allocating any nodes.

Download all files also save the Settings precision for results and percentages.
Both scripts use those digit counts in CSV values and confidence intervals;
older files default to 3 and 1 digits respectively. CSV always uses comma field
separators and dot decimal separators, without thousands separators.

`partitions.txt` lists Elja partitions in preference order. `Nodes` is the
configured number of nodes, `Cores` counts physical cores per node, and
`MaxNode` is the maximum in one allocation (`INF` means no partition limit).
`Speed` is throughput per physical core relative to a mimir core. The five
measured factors use 20,000 Iceland replicates at one process per physical
core; unmeasured factors are provisionally 1 per core. The measured times
(seconds) were mimir 115.562, short 155.994, mimir-interactive 107.766,
gpu-2xA100 129.608, and himem-mimir 109.484.
Each measured `Speed` is `(115.562 / partition time) × (64 / Cores)`.
The inventory was read from Elja's `sinfo` and `scontrol show partition`.

Before trying each partition, `elja.py` queries `sinfo` (as `avail.sh` does)
for fully idle nodes with enough logical CPUs for the exclusive allocation.
It limits requests to that available count and skips partitions with none.
The inquiry is refreshed for each partition, so nodes already allocated
through an earlier partition are no longer counted as idle. Slurm still
decides which nodes to allocate; availability can change after the inquiry.

`elja.py` makes separate one-node requests with `salloc --immediate`,
launching requests concurrently within each partition. It collects that
partition's results before requesting any remaining nodes from the next
partition in preference order.
When `.venv-elja/bin/python` exists in the repository, workers use it even if
the command itself was started with another Python. This environment must be
on the shared filesystem and compatible with every requested node type.
By default it uses only idle nodes. With `-n T -m N`, it requests `T - N`
idle nodes and `N` mixed nodes. If either target cannot be met, it releases
the allocations and exits. It queries
`scontrol show node --json`, orders mixed candidates by free Slurm CPUs, and
requires at least 100 MiB of unreserved memory for each free physical core
(two Slurm CPUs on Elja). Each mixed request is pinned to its node, reserves
100 MiB per simulation process, and shares the remaining node resources.
`-C` also caps the CPU and memory request on mixed nodes. As with idle nodes,
availability can change before Slurm grants the allocation.
For replicate assignment, mixed nodes are estimated at 60% of their
partition's listed per-core speed. Their CPU and memory requests are unchanged.
Mixed-node requests are submitted together for the remaining slots, then
checked together. If a request is refused, another candidate is tried.
Each allocation starts `worker.py`, which waits for its assigned replicate
range and runs `backend/sim.py` once through `srun`. Slurm reserves both
logical CPUs per physical core, while `sim.py -C` receives the physical core
count. Replicates are divided in proportion to each node's process count
times its per-core `Speed`. If a node cannot start immediately, `elja.py`
tries the next partition.

The job directory contains a frozen input snapshot, a manifest, allocation
logs, and one mergeable JSON result per node. `elja.py` checks each node's
seed and replicate range before combining the results.

To create reports later from a retained job, without allocating nodes or
rerunning any simulations:

```sh
./backend/parsim/elja-report.py <job-id> -o results.csv -x results.xlsx
```

The argument may instead be a path to a job directory. A bare job ID is looked
up under `backend/parsim/jobs/`. Either output may be requested alone. The script
reads the manifest's node files, checks their seeds and complete replicate
coverage, and uses the frozen inputs' display precision. Missing or invalid
node results cause an error before reports are written. Extra node files not
listed in the manifest are ignored. Job files are preserved, and no additional
statistics JSON is created. Only the current statistics format is supported.

During simulation, each node writes an atomic `progress-NNN.json` file
every 15 seconds, with completed and assigned replicates and elapsed time.
`elja.py` displays the total progress, finished-node count, elapsed time,
and estimated remaining time. Remaining time uses each node's recent rate
and the longest expected remaining run; it shows `--` until all unfinished
nodes have reported enough progress. Terminal output updates one line;
redirected output records a new line at each update. A final message marks
the start of merging. No extra options are needed for `elja.py`.

For standalone offline runs, `sim.py --progress FILE` writes the same node
progress format. Progress reporting does not change seeds or replicate ranges.
