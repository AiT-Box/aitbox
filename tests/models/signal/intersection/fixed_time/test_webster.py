import numpy as np

from aitbox.models.signal.isolated.cycler.webster import Webster


def test_webster_cycle():
    webster_calc = Webster(min_cycle=50, max_cycle=180)
    l = np.array([5, 5, 5, 5])
    y = np.array([0.16, 0.17, 0.2, 0.15])
    cycle = webster_calc.get_cycle_by_webster(l, y)
    print(f"cycle is {cycle}")