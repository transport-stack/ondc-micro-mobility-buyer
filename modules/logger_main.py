# set logging level in case of dev
"""

CRITICAL	50
ERROR	40
WARNING	30
INFO	20
DEBUG	10
NOTSET	0

If logging is set to INFO,
logs below INFO won't be shown

https://stackoverflow.com/a/13638084/2852369
"""
import logging

from modules.env_main import log_level

logging.getLogger("requests").setLevel(logging.WARNING)

# Disable logs for urllib3.connectionpool
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
# logging_level = logging.INFO
# if is_dev():
# 	logging_level = logging.DEBUG

logging.basicConfig(
    # level=logging_level,
    format="%(name)s - %(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

logger = logging.getLogger("logger_main")
logger.setLevel(log_level)

DEBUG_LEVELV_NUM = 9
logging.addLevelName(DEBUG_LEVELV_NUM, "DEBUGV")


def debugv(self, message, *args, **kws):
    if self.isEnabledFor(DEBUG_LEVELV_NUM):
        # Yes, logger takes its '*args' as 'args'.
        self._log(DEBUG_LEVELV_NUM, message, args, **kws)


logging.Logger.debugv = debugv

logger.info("logging level: {}".format(log_level))
