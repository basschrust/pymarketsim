import sys
from loguru import logger
from datetime import datetime
from marketsim.input import config


# Keep reference to the real console
terminal = sys.stdout

# remove printing to console
logger.remove()

# One file per each run:
logger.add(
    sink=f"{config.output_dir}/main.log",
    format="{elapsed} | {message}",
    level="DEBUG" if config.debug_logging else "INFO",
    filter=lambda record: "market_id" not in record["extra"],
)


class StreamToLogger:
    def write(self, log):
        log = log.strip()
        if log:
            logger.info(log)

    def flush(self):
        pass

sys.stdout = StreamToLogger()
# unhash if you want the errors be shown in the log, not console:
# sys.stderr = StreamToLogger()
