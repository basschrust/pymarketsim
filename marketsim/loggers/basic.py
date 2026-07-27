import sys
from loguru import logger

logger.add("marketsim/output/simulation.log")

class StreamToLogger:
    def write(self, log):
        log = log.strip()
        if log:
            logger.info(log)

    def flush(self):
        pass

sys.stdout = StreamToLogger()
sys.stderr = StreamToLogger()
