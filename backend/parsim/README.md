# Parallel offline simulation

Activate the repository's Python environment, then run from the repository root:

```sh
./backend/parsim/elja.py -a election.json -r 1000 -S 123 -n 10 -o results.csv
```

Use `-v votes.csv -e systems.json -s settings.json` instead of `-a` for
separate input files. The `-r`, `-i`, `-S`, `-o`, and `-O` options have
the same meanings as in `backend/sim.py`. Here `-C` caps simulation processes
per node; by default Elja uses one process per physical core. Run `elja.py`
on Elja; it always uses Slurm. For local multicore simulations, use
`backend/sim.py`.

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
Each allocation starts `worker.py`, which waits for its assigned replicate
range and runs `backend/sim.py` once through `srun`. Slurm reserves both
logical CPUs per physical core, while `sim.py -C` receives the physical core
count. Replicates are divided in proportion to each node's process count
times its per-core `Speed`. If a node cannot start immediately, `elja.py`
tries the next partition.

The job directory contains a frozen input snapshot, a manifest, allocation
logs, and one mergeable JSON result per node. `elja.py` checks each node's
seed and replicate range before combining the results.

During simulation, each node writes an atomic `progress-NNN.json` file
every five seconds, with completed and assigned replicates and elapsed time.
`elja.py` displays the total progress, finished-node count, elapsed time,
and estimated remaining time. Remaining time uses each node's recent rate
and the longest expected remaining run; it shows `--` until all unfinished
nodes have reported enough progress. Terminal output updates one line;
redirected output records a new line at each update. A final message marks
the start of merging. No extra options are needed for `elja.py`.

For standalone offline runs, `sim.py --progress FILE` writes the same node
progress format. Progress reporting does not change seeds or replicate ranges.
