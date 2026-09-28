from __future__ import annotations

import duckdb
import pandas as pd
from sympy.core import parameters

from marketsim.agent import Agent
from marketsim.market import Security
from marketsim.input import config
from marketsim.loggers.basic import terminal

# TODO: create some base class with abstract methods, use instances depending on the configuration
class Repository:
    def __init__(self):
        self.localdb = f"{config.output_dir}/daedalus.duckdb"
        self.prepare_tables()


    def prepare_tables(self):
        conn = duckdb.connect(self.localdb)

        ###### static tables - per simulation  ################

        # securities
        conn.execute("""
            CREATE TABLE IF NOT EXISTS securities (
                    asset_id INTEGER,
                    instrument_class STRING,
                    market_type STRING,
                    name STRING,
                    eod_status STRING,
                    reference_price DOUBLE,
            )
        """)

        # agents - subjects of the simulation
        conn.execute("""
                    CREATE TABLE IF NOT EXISTS agents (
                            agent_id INTEGER,
                            name STRING,
                            group_name STRING,
                    )
                """)

        ##############  dynamic tables - per day mostly   ######################

        # EoD position (portfolio) of each agent, lowercase columns please!
        conn.execute("""
            CREATE TABLE IF NOT EXISTS position_history (
                day       INTEGER,
                time_tick INTEGER,
                agent_id  INTEGER,
                asset_id  INTEGER,
                position  INTEGER,
                position_value DOUBLE
            )
        """)

        # Market situation
        # traded prices # TODO: add volume_by_value (?)
        conn.execute("""
                    CREATE TABLE IF NOT EXISTS traded_prices (
                        day       INTEGER,
                        time_tick INTEGER,
                        asset_id  INTEGER,
                        open      DOUBLE,
                        high      DOUBLE,
                        low       DOUBLE,
                        close     DOUBLE,
                        volume    DOUBLE,
                    )
                """)

        # TODO: eod_prices / eod_traded_prices

        ##### granular tables - may contain significant volumes of data ######################

        # orders
        conn.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        day INTEGER,
                        price DOUBLE,
                        order_type INTEGER,
                        quantity INTEGER,
                        agent_id INTEGER,
                        time INTEGER,
                        order_id INTEGER,
                        asset_id INTEGER,
                        executed_price DOUBLE,
                        executed_mode STRING,
                        parent_id INTEGER,
                        matched_with INTEGER,
                        valid_until INTEGER,
                    )
                """)


        # trades / matched orders
        conn.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        price DOUBLE,
                        time INTEGER,
                        order_id INTEGER,
                        volume INTEGER,
                        cash DOUBLE,
                        phase STRING,
                    )
                """)


        conn.close()

    ##### methods for making data persistent

    def save_security(self, security: Security) -> None:
        with duckdb.connect(self.localdb) as conn:
            conn.execute("""
                INSERT INTO securities (
                    asset_id,
                    instrument_class,
                    market_type,
                    name,
                    eod_status,
                    reference_price
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, parameters=[
                security.asset_id,
                security.instrument_class,
                security.market_type,
                security.name,
                security.eod_status,
                security.reference_price,
            ])

    def save_agent(self, agent: Agent) -> None:
        with duckdb.connect(self.localdb) as conn:
            conn.execute("""
                INSERT INTO agents (
                    agent_id,
                    name,
                    group_name
                )
                VALUES (?, ?, ?)
            """, parameters=[agent.agent_id, agent.name, agent.group_name])

    def save_position_history(self, position_history_df: pd.DataFrame):
        conn = duckdb.connect(self.localdb)
        conn.register("position_history_df", position_history_df)

        conn.execute("""
            INSERT INTO position_history
            SELECT day, agent_id, time_tick, asset_id, position, position_value
            FROM position_history_df
        """)

        conn.unregister("position_history_df")
        conn.close()

    def save_trades(self):
        pass

    def save_traded_prices(self, traded_price_df: pd.DataFrame):
        # TODO: add version for derivatives, including theoretical - needed?
        conn = duckdb.connect(self.localdb)
        conn.register("traded_prices_df", traded_price_df)

        conn.execute("""
            INSERT INTO traded_prices
            SELECT day, time_tick, asset_id, open, high, low, close, volume
            FROM traded_prices_df      
        """)

        conn.unregister("traded_prices_df")
        conn.close()






    # methods for data extraction
