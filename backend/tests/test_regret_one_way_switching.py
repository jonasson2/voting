"""Verify regret selection independently of the vectorised implementation."""
import unittest
import numpy as np
from division_rules import dhondt_gen, sainte_lague_gen
from methods.provisional_allocation import allocate_provisionally, divisor_values
from methods.one_way_switching import regret_one_way_switching

class RegretSwitchingTest(unittest.TestCase):
    def test_counterexample(self):
        final, _ = regret_one_way_switching(
            [[5,27,24],[10,28,1],[13,15,21]], [5]*3, [3,7,5],
            [[0,1,0],[0,1,0],[0,0,1]], dhondt_gen)
        np.testing.assert_array_equal(final, [[0,2,3],[1,4,0],[2,1,2]])

    def test_priorities_and_constraints(self):
        rng = np.random.default_rng(276)
        for rule in (dhondt_gen, sainte_lague_gen):
            for _ in range(60):
                votes = rng.integers(1,1000,(3,4))
                prior = np.eye(3,4,dtype=int)
                targets = np.array([4,4,4,3])
                baseline = allocate_provisionally(votes,[5]*3,prior,rule)
                current = baseline.copy()
                div = divisor_values(rule,5)
                final, demo = regret_one_way_switching(votes,[5]*3,targets,prior,rule)
                for step in demo['data']['switches']:
                    balance = current.sum(0)-targets
                    choices = []
                    for q in np.flatnonzero(balance<0):
                        candidates = []
                        for c in range(3):
                            for p in np.flatnonzero(balance>0):
                                if current[c,p] > prior[c,p]:
                                    loss = (np.log(votes[c,p])-np.log(div[current[c,p]-1])
                                            -np.log(votes[c,q])+np.log(div[current[c,q]]))
                                    candidates.append((loss,c,int(p)))
                        if not candidates:
                            continue
                        candidates.sort()
                        loss,c,p = candidates[0]
                        regret = candidates[1][0]-loss if len(candidates)>1 else np.inf
                        choices.append(((regret,-loss,-c,-p,-q),(c,p,int(q))))
                    _, expected = max(choices)
                    actual = (step['constituency'],step['from'],step['to'])
                    self.assertEqual(actual,expected)
                    c,p,q = actual
                    current[c,p]-=1;current[c,q]+=1
                np.testing.assert_array_equal(current,final)
                np.testing.assert_array_equal(final.sum(0),targets)
                np.testing.assert_array_equal(final.sum(1),[5]*3)
                self.assertTrue((final>=prior).all())
                self.assertEqual(abs(final-baseline).sum(),abs(baseline.sum(0)-targets).sum())
                self.assertEqual(demo['data']['exchanges'],[])

    def test_forced_transfer(self):
        final,_ = regret_one_way_switching([[10,10]],[1],[0,1],[[0,0]],dhondt_gen)
        np.testing.assert_array_equal(final,[[0,1]])
