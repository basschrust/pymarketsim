import duckdb
from marketsim.input import config


# TODO: create some base class with abstract methods, use instances depending on the configuration
class Repository:
    def __init__(self):

        self.prepare_tables()


    def prepare_tables(self):
        conn = duckdb.connect(f"{config.output_dir}/daedalus.duckdb")

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

    def save_position_history(self, agent):
        pass

    def save_trades(self):
        pass


    # methods for data extraction
