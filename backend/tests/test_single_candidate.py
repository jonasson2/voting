from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from apportion import apportion1d_general
from dictionaries import DIVIDER_RULES, QUOTA_RULES
from electionHandler import ElectionHandler
from electionSystem import ElectionSystem
from noweb import load_votes, votes_to_excel
from vote_table import check_vote_table


class SingleCandidateTest(unittest.TestCase):
    def make_table(self):
        table = load_votes('../data/2-by-2-example.csv')
        table['constituencies'] = [
            {'name': 'One', 'num_fixed_seats': 3, 'num_adj_seats': 0}]
        table['votes'] = [[100, 1]]
        table['pruned'] = [0]
        table['independent_candidates'] = [True, False]
        return check_vote_table(table)

    def test_generic_fixed_allocation_caps_candidate_for_divisor_and_quota(self):
        table = self.make_table()
        for rule in ('dhondt', 'hare'):
            with self.subTest(rule=rule):
                system = ElectionSystem()
                system.copy_info_from_votes(table)
                system['primary_divider'] = rule
                election = ElectionHandler(table, [system], True).elections[0]
                self.assertEqual(election.results['fixed_const_seats'], [[1, 2]])

    def test_national_fixed_seats_exclude_candidate(self):
        table = self.make_table()
        table['party_vote_info'].update(
            specified=True, name='National', num_fixed_seats=2,
            num_adj_seats=0, votes=[100, 1])
        table = check_vote_table(table)
        system = ElectionSystem()
        system.copy_info_from_votes(table)
        election = ElectionHandler(table, [system], True).elections[0]
        self.assertEqual(election.results['fixed_nat_seats'], [0, 2])

    def test_candidate_may_have_votes_in_only_one_constituency(self):
        table = self.make_table()
        table['constituencies'].append(
            {'name': 'Two', 'num_fixed_seats': 1, 'num_adj_seats': 0})
        table['votes'].append([1, 10])
        table['pruned'].append(0)
        with self.assertRaisesRegex(ValueError, 'only one constituency'):
            check_vote_table(table)

    def test_excel_round_trip_uses_new_label(self):
        table = self.make_table()
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'votes.xlsx'
            votes_to_excel(table, path)
            self.assertEqual(load_votes(path)['independent_candidates'], [True, False])

    def test_apportionment_respects_existing_candidate_seat(self):
        for rule, rule_type in ((DIVIDER_RULES['dhondt'], 'Division'),
                                (QUOTA_RULES['hare'], 'Quota')):
            with self.subTest(rule_type=rule_type):
                allocation, _, _ = apportion1d_general(
                    [100, 1], 3, [1, 0], rule, rule_type,
                    max_seats=[1, 3])
                self.assertEqual(allocation.tolist(), [1, 2])


if __name__ == '__main__':
    unittest.main()
