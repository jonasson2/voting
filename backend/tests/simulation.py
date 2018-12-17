# coding:utf-8
from unittest import TestCase
from random import uniform

import logging
import simulate
import voting
import util


class SimulationTest(TestCase):
    def setUp(self):
        pass

    def test_generate_votes(self):
        pass
        # Generate a few vote sets

    def test_generate_votes_average(self):
        s_rules = simulate.SimulationRules()
        s_rules["simulation_count"] = 1000
        e_rules = voting.ElectionRules()
        e_rules["constituency_names"] = ["I", "II", "III"]
        e_rules["constituency_seats"] = [5, 6, 4]
        e_rules["constituency_adjustment_seats"] = [1, 2, 1]
        e_rules["parties"] = ["A", "B"]
        votes = [[500, 300], [200, 400], [350, 450]]
        sim = simulate.Simulation(s_rules, [e_rules], votes, 100)
        gen = sim.gen_votes()
        r = []
        r_avg = []
        r_var = []
        for k in range(s_rules["simulation_count"]):
            r.append([])
            generated_votes = next(gen)
            for i in range(len(votes)):
                r[k].append([])
                for j in range(len(votes[i])):
                    r[k][i].append(uniform(0.0,1.0))
        for i in range(len(votes)):
            r_avg.append([])
            r_var.append([])
            for j in range(len(votes[i])):
                r_ij = [r[k][i][j] for k in range(s_rules["simulation_count"])]
                # average = simulate.avg(r_ij)
                # r_avg[i].append(average)
                # r_var[i].append(simulate.var(r_ij, average))

        sim.test_generated()
        # r_avg_error = simulate.error(r_avg, 0.5)
        # r_var_error = simulate.error(r_var, 1/12.0)

        # self.assertLessEqual(r_avg_error, 0.01)


        # Verify that µ=0.5±2%

    def test_simulate_once(self):
        #Arrange
        s_rules = simulate.SimulationRules()
        s_rules["simulation_count"] = 1
        e_rules = voting.ElectionRules()
        e_rules["constituency_names"] = ["I", "II", "III"]
        e_rules["constituency_seats"] = [5, 6, 4]
        e_rules["constituency_adjustment_seats"] = [1, 2, 1]
        e_rules["parties"] = ["A", "B"]
        votes = [[500, 300], [200, 400], [350, 450]]
        sim = simulate.Simulation(s_rules, [e_rules], votes, 100)
        #Act
        sim.simulate()
        #Assert
        result = sim.get_results_dict()
        vote_data = result['vote_data']['sim_votes']
        list_measures = result['data'][0]['list_measures']
        for const in range(sim.num_constituencies):
            for party in range(sim.num_parties):
                self.assertGreater(vote_data['sum'][const][party], 0)
                self.assertGreater(vote_data['avg'][const][party], 0)
                self.assertEqual(vote_data['cnt'][const][party], 1)
                self.assertEqual(vote_data['var'][const][party], 0)
                self.assertEqual(vote_data['std'][const][party], 0)
                for m in simulate.LIST_MEASURES.keys():
                    self.assertEqual(list_measures[m]['cnt'][const][party], 1)
                    self.assertEqual(list_measures[m]['var'][const][party], 0)
                    self.assertEqual(list_measures[m]['std'][const][party], 0)
        measures = result['data'][0]['measures']
        for m in simulate.MEASURES.keys():
            self.assertEqual(measures[m]['cnt'], 1)
            self.assertEqual(measures[m]['var'], 0)
            self.assertEqual(measures[m]['std'], 0)
