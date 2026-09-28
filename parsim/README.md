# Parallel offline simulation

Activate the repository's Python environment, then run a local job:

```sh
./parsim/run.py -a election.json -r 1000 -C 8 -S 123 -o results.csv
```

`-a` accepts a Download all file. Alternatively, use `-v votes.csv -e
systems.json -s settings.json`. `-r` sets the total replicates; `-C` is the
number of concurrent local workers. `--chunk-size` controls replicates per
independent chunk. If the settings have no seed, or `-S -` is given, the master
chooses one and records it in `manifest.json`.

The master prints the job directory. It contains a frozen input snapshot,
manifest, and one JSON result per chunk. If a chunk fails, rerun that number:

```sh
./parsim/worker.py parsim/jobs/JOB_ID 3
./parsim/merge.py parsim/jobs/JOB_ID -o results.csv
```

The merger checks job identity, input and source hashes, replicate ranges, and
completion before combining the accumulated statistics. The same worker and
merger can be used when a later launcher sends chunks to different nodes.
