from histo import Histo_int, Histo_bins
import numpy as np
rng = np.random.default_rng()
randoms1 = rng.random(30)
randoms2 = rng.random(30)
h = Histo_bins(0, 1)
g = Histo_bins(0, 1, 3)

for x in randoms1:
    h.update(x)
for (x,y) in zip(randoms1, randoms2):
    g.update([x, x, y]) 
q0 = h.get_quantile(0)
q10 = h.get_quantile(0.1)
q99 = h.get_quantile(0.99)
q100 = h.get_quantile(1)

p0 = g.get_quantile(0)
p1 = g.get_quantile(0.01)
p100 = g.get_quantile(1)

print(q0, q10, q99, q100)
print(p0, p1, p100)
pass