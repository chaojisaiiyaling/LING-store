from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    name: str

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return dataframe with signal column: 1 buy, -1 sell, 0 hold."""


def cross_up(left: pd.Series, right: pd.Series) -> pd.Series:
    return (left.shift(1) <= right.shift(1)) & (left > right)


def cross_down(left: pd.Series, right: pd.Series) -> pd.Series:
    return (left.shift(1) >= right.shift(1)) & (left < right)
