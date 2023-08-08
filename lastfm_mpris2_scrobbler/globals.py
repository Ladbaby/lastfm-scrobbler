import time
import datetime
import logging

logger = logging.getLogger("dbus-scrobbler")

def get_unix_timestamp():
    return int(time.mktime(datetime.datetime.now().timetuple()))