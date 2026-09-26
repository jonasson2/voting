from types import SimpleNamespace
import unittest

import numpy as np

from simulate import Collect, Simulation


class AbsoluteMeasureTest(unittest.TestCase):
    def test_absolute_seat_share_measures_are_halved(self):
        simulation = object.__new__(Simulation)
        simulation.nparty = 2
        simulation.party_votes_specified = True
        election = SimpleNamespace(
            nconst=2,
            votes=[[10, 10], [10, 10]],
            ref_seat_shares=np.array([[1, 1], [1, 1]]),
            total_ref_const=[2, 2],
            total_ref_nat=[2, 2],
            total_ref_seat_shares=[3, 5],
            results={
                'all_const_seats': [[2, 0], [0, 2]],
                'all_const_total': [3, 1],
                'all_nat_seats': [1, 3],
                'all_grand_total': [4, 4],
            },
        )
        deviations = Collect()

        simulation.seats_minus_shares_measures(election, 0, deviations)

        self.assertEqual(deviations['sum_abs'], [2])
        self.assertEqual(deviations['sum_sq'], [4])
        for extension in ('const', 'nat', 'overall'):
            with self.subTest(extension=extension):
                self.assertEqual(
                    deviations[f'sum_abs_party_{extension}'], [1])
                self.assertEqual(
                    deviations[f'sum_sq_party_{extension}'], [2])

    def test_only_between_system_comparisons_are_halved(self):
        simulation = object.__new__(Simulation)
        simulation.party_votes_specified = True
        first = SimpleNamespace(results={
            'all_const_seats': [[2, 0], [0, 2]],
            'all_const_total': [3, 1],
            'all_nat_seats': [1, 3],
            'all_grand_total': [4, 4],
        })
        second = SimpleNamespace(results={
            'all_const_seats': [[1, 1], [1, 1]],
            'all_const_total': [1, 3],
            'all_nat_seats': [3, 1],
            'all_grand_total': [2, 6],
        })
        deviations = Collect()

        simulation.add_deviation(first, second, 'cmp_Second', deviations)
        simulation.add_deviation(first, second, 'dev_ref', deviations)

        for extension in ('const', 'tot', 'nat', 'grand'):
            with self.subTest(extension=extension):
                self.assertEqual(deviations[f'cmp_Second_{extension}'], [2])
                self.assertEqual(deviations[f'dev_ref_{extension}'], [4])


if __name__ == '__main__':
    unittest.main()
