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
        Columns: Open, High, Low, Close, Volume.
    """
    fig, (ax_price, ax_volume) = plt.subplots(
        2,
        1,
        figsize=(12, 7),
        sharex=True,
        gridspec_kw={"height_ratios": [4, 1]},
    )

    candle_width = 0.7

    for t, row in df.iterrows():
        o = float(row["Open"])
        h = float(row["High"])
        l = float(row["Low"])
        c = float(row["Close"])

        color = "#26a69a" if c >= o else "#ef5350"

        # Wick
        ax_price.plot([t, t], [l, h], color=color, linewidth=1)

        # Candle body
        bottom = min(o, c)
        height = abs(c - o)

        # Prevent invisible body when open == close
        if height == 0:
            height = 0.001

        # ax_price.add_patch(
        #     Rectangle(
        #         (t - candle_width / 2, bottom),
        #         candle_width,
        #         height,
        #         facecolor=color,
        #         edgecolor="black",
        #     )
        # )

        body = Rectangle(
            (t - candle_width / 2, bottom),
            candle_width,
            height,
            facecolor=color,
            edgecolor=color,
            linewidth=1,
        )

        ax_price.add_patch(body)

        # Volume
        ax_volume.bar(
            t,
            row["Volume"],
            width=candle_width,
            color=color,
            align="center",
        )

    ax_price.set_title(title)
    ax_price.set_ylabel("Price")
    ax_price.grid(True, alpha=0.3)

    ax_volume.set_ylabel("Volume")
    ax_volume.set_xlabel("Simulation time")
    ax_volume.grid(True, alpha=0.3)

    ax_price.set_xlim(df.index.min() - 1, df.index.max() + 1)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150)

    plt.close(fig)
