from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd
import mplfinance as mpf
from pathlib import Path
import math
import numpy as np


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
            for price, volume in items: # TODO: these are yet price, order_id (!!!) - solved (?)
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


def plot_by_type(
    orders_by_type: dict,
    output_file: str,
    title: str,
    mode: str = "simple",  # or extended
) -> None:
    """
    Plot order statistics by agent/type.

    Simple input:
        {
            "MM": {
                "Count_buy": 6,
                "Volume_buy": 67,
                "Count_sell": 7,
                "Volume_sell": 89,
            },
            ...
        }

    Extended input:
        {
            "group1": {
                "Count_buy": {
                    "arrived": 60,
                    "waited": 40,
                },
                "Volume_buy": {
                    "arrived": 20,
                    "waited": 0,
                },
                "Count_sell": {
                    "arrived": 10,
                    "waited": 20,
                },
                "Volume_sell": {
                    "arrived": 20,
                    "waited": 20,
                },
            },
            ...
        }
    """

    if mode not in ("simple", "extended"):
        raise ValueError(
            f"Unknown mode '{mode}'. Expected 'simple' or 'extended'."
        )

    order_types = list(orders_by_type.keys())

    fig, (ax_count, ax_volume) = plt.subplots(
        2,
        1,
        figsize=(10, 8),
        sharex=True,
    )

    x = list(range(len(order_types)))
    width = 0.35

    if mode == "simple":

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

    else:
        # Extract extended data
        buy_count_arrived = [
            orders_by_type[order_type]["Count_buy"]["arrived"]
            for order_type in order_types
        ]
        buy_count_waited = [
            orders_by_type[order_type]["Count_buy"]["waited"]
            for order_type in order_types
        ]

        sell_count_arrived = [
            orders_by_type[order_type]["Count_sell"]["arrived"]
            for order_type in order_types
        ]
        sell_count_waited = [
            orders_by_type[order_type]["Count_sell"]["waited"]
            for order_type in order_types
        ]

        buy_volume_arrived = [
            orders_by_type[order_type]["Volume_buy"]["arrived"]
            for order_type in order_types
        ]
        buy_volume_waited = [
            orders_by_type[order_type]["Volume_buy"]["waited"]
            for order_type in order_types
        ]

        sell_volume_arrived = [
            orders_by_type[order_type]["Volume_sell"]["arrived"]
            for order_type in order_types
        ]
        sell_volume_waited = [
            orders_by_type[order_type]["Volume_sell"]["waited"]
            for order_type in order_types
        ]

        # Order count - Buy
        ax_count.bar(
            [i - width / 2 for i in x],
            buy_count_arrived,
            width=width,
            label="Buy arrived",
            color="blue",
        )

        ax_count.bar(
            [i - width / 2 for i in x],
            buy_count_waited,
            width=width,
            bottom=buy_count_arrived,
            label="Buy waited",
            color="lightblue",
        )

        # Order count - Sell
        ax_count.bar(
            [i + width / 2 for i in x],
            sell_count_arrived,
            width=width,
            label="Sell arrived",
            color="darkred",
        )

        ax_count.bar(
            [i + width / 2 for i in x],
            sell_count_waited,
            width=width,
            bottom=sell_count_arrived,
            label="Sell waited",
            color="lightcoral",
        )

        # Order volume - Buy
        ax_volume.bar(
            [i - width / 2 for i in x],
            buy_volume_arrived,
            width=width,
            label="Buy arrived",
            color="blue",
        )

        ax_volume.bar(
            [i - width / 2 for i in x],
            buy_volume_waited,
            width=width,
            bottom=buy_volume_arrived,
            label="Buy waited",
            color="lightblue",
        )

        # Order volume - Sell
        ax_volume.bar(
            [i + width / 2 for i in x],
            sell_volume_arrived,
            width=width,
            label="Sell arrived",
            color="darkred",
        )

        ax_volume.bar(
            [i + width / 2 for i in x],
            sell_volume_waited,
            width=width,
            bottom=sell_volume_arrived,
            label="Sell waited",
            color="lightcoral",
        )

    # Common formatting
    ax_count.set_ylabel("Count")
    ax_count.set_title(title)
    ax_count.grid(axis="y")
    ax_count.legend()

    ax_volume.set_ylabel("Volume")
    ax_volume.set_xlabel("Type")
    ax_volume.grid(axis="y")
    ax_volume.legend()

    ax_volume.set_xticks(x)
    ax_volume.set_xticklabels(order_types)

    fig.tight_layout()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def plot_bid_ask(
    bid_ask: dict[int, list[float]],
    output_file: str,
    title: str = "Bid ask",
    clip_value: float = 3.0,
) -> None:
    """
    Plot best bid and best ask over simulation time.

    Args:
        bid_ask: {
            time_tick: [best_bid, best_ask],
            ...
        }
        output_file: Output PNG filename.
        clip_value: Value used to clip +/-inf values.
    """
    times = sorted(bid_ask)
    spreads = []

    for time in times:
        bid, ask = bid_ask[time]

        spread = float(ask) - float(bid)

        if not math.isfinite(spread):
            spread = clip_value

        spreads.append(spread)

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(times, spreads, label="Spread")

    ax.set_xlabel("Simulation time")
    ax.set_ylabel("Spread")
    ax.grid(True)
    ax.legend()
    ax.set_title(title)

    fig.tight_layout()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def plot_realized_volatility(
    volatility: dict,
    output_file: str,
    title: str = "Realized volatility",
) -> None:
    if not volatility:
        return

    times = sorted(volatility)
    values = [volatility[t] for t in times]

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(times, values, label="Realized volatility")

    ax.set_xlabel("Simulation time")
    ax.set_ylabel("Realized volatility")
    ax.set_title(title)
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_file, dpi=150)
    plt.close(fig)


def plot_agent_profitability_vs_volatility(
    agents: list,
    output_file: str,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))

    groups = defaultdict(list)

    for agent in agents:
        history = agent.position_value_history

        if len(history) < 2:
            continue

        # Make sure observations are ordered by simulation time
        values = np.array(
            [float(v) for _, v in sorted(history.items())],
            dtype=float,
        )

        # Portfolio returns between consecutive simulation ticks
        returns = values[1:] / values[:-1] - 1

        volatility = np.std(returns)

        # Total profitability over the simulation
        profitability = values[-1] / values[0] - 1

        groups[agent.group].append(
            (volatility, profitability, agent.agent_id)
        )

    for group, points in groups.items():
        x = [p[0] for p in points]
        y = [p[1] for p in points]

        ax.scatter(x, y, label=str(group), alpha=0.8)

    ax.axhline(0, linewidth=0.8)
    ax.axvline(0, linewidth=0.8)

    ax.set_xlabel("Portfolio volatility")
    ax.set_ylabel("Profitability")
    ax.set_title("Agent Profitability vs Portfolio Volatility")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Group")

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
