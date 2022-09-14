# instantiate and configure the worker pool
from time import sleep
from pathos.pools import ProcessPool
pool = ProcessPool(nodes=4)
# do a blocking map on the choseqn function
results = pool.map(pow, [1,2,3,4], [5,6,7,8])
print(results)
# do a non-blocking map, then extract the results from the iterator
results = pool.uimap(pow, [1,2,3,4,5,6,7,8,9,10], list(range(10)))
results = list(results)
print(results)
pool.close()
