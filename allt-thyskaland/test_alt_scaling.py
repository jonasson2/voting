from alternating_scaling import alt_scaling_new
from division_rules import sainte_lague_gen
import numpy as np
import json
from germany_methods import gurobi_optimal_const
from table_util import entropy_single
info = json.load(open('alt_scaling_failure.json'))
votes = np.array(info["votes"])
votes = np.round(votes).astype(int)
rowsums = np.array(info["rowsum"], int)
colsums = np.array(info["colsum"], int)
prior_alloc = np.zeros(votes.shape, int)
div_gen = sainte_lague_gen()
N = max(max(rowsums), max(colsums)) + 1
div = np.array([next(div_gen) for i in range(N + 1)])
alloc = alt_scaling_new(votes, rowsums, colsums, prior_alloc, div)
for c in range(-3,0):
    alloc[c,0] = 0
    alloc[c,2] = 1
selected = [a.index(1) for a in alloc.tolist()]

selected_gurobi = gurobi_optimal_const(votes, colsums)
print('selected-alt-scal:', selected)
print('selected-gurobi:  ', selected_gurobi)

entropy_as = entropy_single(votes, selected)
entropy_gur = entropy_single(votes, selected_gurobi)
print(f'Entropy alt-scal: {entropy_as:.3f}')
print(f'Entropy gurobi:   {entropy_gur:.3f}')
pass
