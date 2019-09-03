#!python3
"""corn calculates value of OTC corn contract"""

import itertools

import matplotlib.pyplot as plt
import more_itertools
import numpy as np
import pandas

from pandas.tseries.offsets import CustomBusinessDay
# from datetime import datetime

from cal import USTradingCalendar


def generate_dts(basis_date, start_date, end_date):
    """gfenerate the dts given the start and end days."""

    # skip non-business days / holidays
    us_bd = CustomBusinessDay(calendar=USTradingCalendar())
    date_range = pandas.bdate_range(start_date, end_date, freq=us_bd)

    # calculate time since basis day (in years)
    diffs = date_range - pandas.to_datetime(basis_date)
    years_since = [x.days/365.25 for x in diffs]

    # for each day, produce the
    diffs = itertools.chain([0], years_since)
    diffs = [b-a for (a, b) in more_itertools.windowed(diffs, n=2, step=1)]
    return date_range, np.asfarray(diffs), np.asfarray(years_since)

class Simulator:
    """Simulates the OTC contracts."""
    def __init__(
            self,
            basis_date="08-27-2019",
            start_date="08-28-2019",
            end_date="11-20-2020",
            volatility=0.16,
            risk_free_rate=0.025,
            start_price=394.75,
            acc_level=420.0,
            ko_level=379.0):
        """simulate simulates a contract's life."""
        self.date_range, self.dts, self.since = generate_dts(
                basis_date, start_date, end_date)
        self.dts_sqrt = np.sqrt(self.dts)
        self.sigma = volatility
        self.sigma_sq = np.square(self.sigma)
        self.r = risk_free_rate
        self.s = start_price
        self.acc_level = acc_level
        self.ko_level = ko_level

        self.eps = np.empty_like(self.dts)
        self.settlements = np.empty_like(self.dts)

    def simulate(self, n):
        def doit():
            self.fill_settlements()
            return self.european_price()
        return np.asfarray([doit() for _ in range(0, n)])

    def fill_settlements(self):
        """get settlements."""
        self.eps[:] = np.exp((self.r - 0.5 * self.sigma_sq)*self.dts+self.sigma * self.dts_sqrt * np.random.normal(size=self.dts.shape))
        s = self.s
        for (i, ep) in enumerate(self.eps):
            s = ep * s
            self.settlements[i] = s

    def plot_settlements(self):
        """plot the settlements, acc, and ko levels"""
        ts = pandas.Series(self.settlements, index=self.date_range)
        ts.plot()
        plt.hlines([self.acc_level, self.ko_level], self.date_range[0], self.date_range[-1])
        plt.show()

    def european_price(self):
        """calculate the price of the european contract"""
        total = 0.0
        # self.settlements[self.settlements > self.acc_level]
        for (i, settlement) in enumerate(self.settlements):
            if settlement > self.acc_level:
                total += 2*(self.acc_level-settlement) * np.exp(-self.r * self.since[i])
            elif settlement > self.ko_level:
                total += self.acc_level - settlement * np.exp(-self.r * self.since[i])
        return total
