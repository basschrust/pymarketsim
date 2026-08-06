import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
from pathlib import Path

def simple_plot_old(x: list, y: list, output_file: str) -> None:
    plt.plot(x, y)
    plt.savefig(output_file)

def simple_plot(
    x: list,
    y: list,
    output_file: str,
    ax=None,
    label: str = None,
    ylabel: str = "Portfolio value",
) -> None:

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
    else:
        fig = ax.figure

    ax.plot(x, y, label=label)

    ax.set_xlabel("Simulation time")
    ax.set_ylabel(ylabel)
    ax.grid(True)

    if label is not None:
        ax.legend()

    fig.tight_layout()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
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
