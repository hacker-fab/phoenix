"""Deterministic, dependency-free tests for simulated furnace cooling."""

import math
import unittest

from sim import ThermalModel, simulate_profile


class TestExponentialCooling(unittest.TestCase):
    def test_coarse_timestep_cools_toward_ambient(self):
        model = ThermalModel(ambient=25.0, max_heating_rate=10.0, cooling_coeff=0.01)
        profile = [(0.0, 500.0), (200.0, 25.0)]
        times, temperatures, _, pwm_values, _ = simulate_profile(
            profile, model, sim_time=400.0, dt=200.0
        )
        self.assertEqual(times, [0.0, 200.0])
        self.assertEqual(pwm_values, [1.0, 0.0])
        first = 25.0 + 1000.0 * (1.0 - math.exp(-2.0))
        second = 25.0 + (first - 25.0) * math.exp(-2.0)
        self.assertAlmostEqual(temperatures[0], first, places=9)
        self.assertAlmostEqual(temperatures[1], second, places=9)
        self.assertGreaterEqual(min(temperatures), model.ambient)

    def test_no_cooling_uses_linear_heating(self):
        model = ThermalModel(ambient=25.0, max_heating_rate=10.0, cooling_coeff=0.0)
        _, temperatures, _, pwm_values, _ = simulate_profile(
            [(0.0, 500.0)], model, sim_time=2.0, dt=2.0
        )
        self.assertEqual(pwm_values, [1.0])
        self.assertEqual(temperatures, [45.0])

    def test_no_heating_stays_at_ambient(self):
        model = ThermalModel(ambient=25.0, max_heating_rate=0.0, cooling_coeff=0.01)
        _, temperatures, _, pwm_values, _ = simulate_profile(
            [(0.0, 100.0)], model, sim_time=600.0, dt=200.0
        )
        self.assertEqual(temperatures, [25.0, 25.0, 25.0])
        self.assertEqual(pwm_values, [1.0, 1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
