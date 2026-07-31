import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf

def simple_plot_old(x: list, y: list, output_file: str) -> None:
    plt.plot(x, y)
    plt.savefig(output_file)

def simple_plot(x: list, y: list, output_file: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(x, y)

    ax.set_xlabel("Simulation time")
    ax.set_ylabel("Portfolio value")
    ax.grid(True)

    fig.tight_layout()
    fig.savefig(output_file, dpi=150)
    plt.close(fig)

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
