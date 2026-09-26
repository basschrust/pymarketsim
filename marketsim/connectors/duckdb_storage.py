import duckdb
import pandas as pd

from marketsim.input import config
from marketsim.loggers.basic import terminal

# TODO: create some base class with abstract methods, use instances depending on the configuration
class Repository:
    def __init__(self):
        self.localdb = f"{config.output_dir}/daedalus.duckdb"
        self.prepare_tables()


    def prepare_tables(self):
        conn = duckdb.connect(self.localdb)

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

        # Market tables
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


        # trades




        conn.close()

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


    # methods for data extraction
