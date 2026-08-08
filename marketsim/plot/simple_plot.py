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

def plot_agent_history(
    position_history: dict,
    value_history: dict,
    output_file: str,
) -> None:

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(10, 8),
        sharex=True,
    )

    # Position subplot
    ax1.plot(
        list(position_history.keys()),
        list(position_history.values()),
    )
    ax1.set_ylabel("Position")
    ax1.grid(True)

    # Portfolio value subplot
    ax2.plot(
        list(value_history.keys()),
        list(value_history.values()),
    )
    ax2.set_xlabel("Simulation time")
    ax2.set_ylabel("Portfolio value")
    ax2.grid(True)

    fig.tight_layout()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def plot_order_book(
    bids: dict,
    asks: dict,
    output_file: str,
    cumulative: bool = True,
) -> None:
    """
    bids and asks should be dictionaries:
        {price: volume}

    If cumulative=True, the values are first converted to cumulative depth.
    """

    def make_depth(book, reverse):
        items = sorted(book.items(), reverse=reverse)

        if cumulative:
            total = 0
            depth = []
            for price, volume in items:
                total += volume
                depth.append((float(price), total))
            return depth

        return [(float(price), volume) for price, volume in items]

    bid_depth = make_depth(bids, reverse=True)
    ask_depth = make_depth(asks, reverse=False)

    fig, ax = plt.subplots(figsize=(12, 6))

    if bid_depth:
        ax.bar(
            [p for p, _ in bid_depth],
            [v for _, v in bid_depth],
            width=0.01,
            color="royalblue",
            label="Bids",
        )

    if ask_depth:
        ax.bar(
            [p for p, _ in ask_depth],
            [v for _, v in ask_depth],
            width=0.01,
            color="darkred",
            label="Asks",
        )

    ax.set_xlabel("Price")
    ax.set_ylabel("Cumulative volume" if cumulative else "Volume")
    ax.set_title("Order Book")
    ax.grid(axis="y")
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
