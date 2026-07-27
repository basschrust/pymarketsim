import sys
from loguru import logger
from datetime import datetime

# remove printing to console
logger.remove()

# One file per each run:
log_filename = datetime.now().strftime("main_%Y%m%d_%H%M%S")

logger.add(f"marketsim/output/{log_filename}.log")

class StreamToLogger:
    def write(self, log):
        log = log.strip()
        if log:
            logger.info(log)

    def flush(self):
        pass

sys.stdout = StreamToLogger()
sys.stderr = StreamToLogger()
