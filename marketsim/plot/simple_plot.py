import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf

def simple_plot(x: list, y: list, output_file: str) -> None:
    plt.plot(x, y)
    plt.savefig(output_file)

class Plotter:
    def line(self, x: list, y: list, output_file: str) -> None:
        plt.plot(x, y)
        plt.savefig(output_file)

    def candles(self, df: pd.DataFrame, output_file: str) -> None:
        pass

    def scatter(self, df: pd.DataFrame, output_file: str) -> None:
        pass

    def hist(self, df: pd.DataFrame, output_file: str) -> None:
        pass
