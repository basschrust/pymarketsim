import sys
from loguru import logger
from datetime import datetime
from marketsim.input import config

# remove printing to console
logger.remove()

# One file per each run:
# log_dir = datetime.now().strftime("run_%Y%m%d_%H%M%S")


logger.add(f"{config.output_dir}/main.log",
           format="{elapsed} | {message}",) # elapsed is timedelta, doesn't understand {HH:mm:ss.SSS}

class StreamToLogger:
    def write(self, log):
        log = log.strip()
        if log:
            logger.info(log)

    def flush(self):
        pass

sys.stdout = StreamToLogger()
# sys.stderr = StreamToLogger()
