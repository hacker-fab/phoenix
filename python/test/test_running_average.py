import pytest
from running_average import RunningAverage


def test_simple():
    y = RunningAverage(5)
    for i in range(5):
        y.add(i)
    assert y.average() == 2.0

    y.clear()
    assert y.average() == 0
