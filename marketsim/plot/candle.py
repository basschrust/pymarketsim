import pandas as pd
import mplfinance as mpf

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def plot_candlestick_old(df, output_file: str):
    fig, axlist =mpf.plot(
        df,
        type='candle',
        volume=True,
        style='yahoo',
        returnfig=True,
    )

    fig.savefig(output_file, dpi=150, bbox_inches="tight")



def plot_candlestick(df: pd.DataFrame, output_file: str | None =None, title: str ="Candlestick chart"):
    """
    Parameters
    ----------
    df : pandas.DataFrame
        Index = integer simulation time.
        Columns: open, high, low, close.
    """

    fig, ax = plt.subplots(figsize=(12, 6))

    candle_width = 0.7

    for t, row in df.iterrows():
        o = float(row["Open"])
        h = float(row["High"])
        l = float(row["Low"])
        c = float(row["Close"])

        # High-low wick
        ax.plot([t, t], [l, h], linewidth=1)

        # Candle body
        bottom = min(o, c)
        height = abs(c - o)

        # Prevent invisible body when open == close
        if height == 0:
            height = 0.001

        body = Rectangle(
            (t - candle_width / 2, bottom),
            candle_width,
            height,
            fill=False if c >= o else True
        )

        ax.add_patch(body)

    ax.set_title(title)
    ax.set_xlabel("Simulation time")
    ax.set_ylabel("Price")

    ax.grid(True)

    ax.set_xlim(df.index.min() - 1, df.index.max() + 1)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150)

    plt.close(fig)
