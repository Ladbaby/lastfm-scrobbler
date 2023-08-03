import time
import datetime
import logging
import coloredlogs

logger = logging.getLogger("dbus-scrobbler")
coloredlogs.install(level="DEBUG", logger=logger)

def get_unix_timestamp():
    return int(time.mktime(datetime.datetime.now().timetuple()))