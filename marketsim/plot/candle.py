import pandas as pd
import mplfinance as mpf

def plot_candlestick(df, output_file: str):
    fig, axlist =mpf.plot(
        df,
        type='candle',
        volume=True,
        style='yahoo',
        returnfig=True,
    )

    fig.savefig(output_file, dpi=150, bbox_inches="tight")
