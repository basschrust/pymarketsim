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
    title: str = "Order Book",
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

    ax.set_xlabel("Price limit")
    ax.set_ylabel("Cumulative volume" if cumulative else "Volume")
    ax.set_title(title)
    ax.grid(axis="y")
    ax.legend()

    fig.tight_layout()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)

def plot_orders_by_type(
    orders_by_type: dict,
    output_file: str,
) -> None:
    """
    Plot order statistics by agent/type.

    Expected input:
        {
            "MM": {
                "Count_buy": 6,
                "Volume_buy": 67,
                "Count_sell": 7,
                "Volume_sell": 89,
            },
            "HBL": {
                "Count_buy": 23,
                "Volume_buy": 250,
                "Count_sell": 2,
                "Volume_sell": 65,
            },
            ...
        }
    """

    order_types = list(orders_by_type.keys())

    buy_counts = [
        orders_by_type[order_type]["Count_buy"]
        for order_type in order_types
    ]
    sell_counts = [
        orders_by_type[order_type]["Count_sell"]
        for order_type in order_types
    ]

    buy_volumes = [
        orders_by_type[order_type]["Volume_buy"]
        for order_type in order_types
    ]
    sell_volumes = [
        orders_by_type[order_type]["Volume_sell"]
        for order_type in order_types
    ]

    fig, (ax_count, ax_volume) = plt.subplots(
        2,
        1,
        figsize=(10, 8),
        sharex=True,
    )

    x = range(len(order_types))
    width = 0.35

    # Order count
    ax_count.bar(
        [i - width / 2 for i in x],
        buy_counts,
        width=width,
        label="Buy",
        color="blue",
    )

    ax_count.bar(
        [i + width / 2 for i in x],
        sell_counts,
        width=width,
        label="Sell",
        color="darkred",
    )

    ax_count.set_ylabel("Number of orders")
    ax_count.set_title("Orders by type")
    ax_count.grid(axis="y")
    ax_count.legend()

    # Order volume
    ax_volume.bar(
        [i - width / 2 for i in x],
        buy_volumes,
        width=width,
        label="Buy",
        color="blue",
    )

    ax_volume.bar(
        [i + width / 2 for i in x],
        sell_volumes,
        width=width,
        label="Sell",
        color="darkred",
    )

    ax_volume.set_ylabel("Volume")
    ax_volume.set_xlabel("Order type")
    ax_volume.grid(axis="y")
    ax_volume.legend()

    ax_volume.set_xticks(list(x))
    ax_volume.set_xticklabels(order_types)

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
