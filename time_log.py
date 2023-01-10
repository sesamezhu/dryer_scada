import logging.config
import datetime
import threading
import os
import sys

previous_map = {"": datetime.datetime.now()}
if not os.path.exists("logs/"):
    print(os.makedirs("logs/"))
logging.config.fileConfig('configs/logging.conf')
console_log = logging.getLogger('console')
time_log_log = logging.getLogger('time')


def now_compact():
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d_%H%M%S.%f')


class DualLogger(object):
    def __init__(self):
        self.terminal = sys.stdout

    def write(self, message):
        self.terminal.write(message)
        console_log.debug(message)

    def flush(self):
        self.terminal.flush()

    def console(self, message):
        self.terminal.write(message)


class ErrLogger(object):
    def __init__(self):
        self.terminal = sys.stderr

    def write(self, message):
        # logged = error_logged_map.get(threading.get_ident(), False)
        # if not logged:
        # error_logged_map[threading.get_ident()] = True
        self.terminal.write(message)
        console_log.error(message)

    def flush(self):
        self.terminal.flush()

    def console(self, message):
        self.terminal.write(message)


__dual_log = DualLogger()
sys.stdout = __dual_log
__error_log = ErrLogger()
sys.stderr = __error_log


def time_key(s, key, _log):
    if s is None:
        return
    if isinstance(s, str):
        s = s.rstrip()
    if key is None:
        key = ""
    now = datetime.datetime.now()
    previous_log = previous_map.get(key, now)
    elapse = now - previous_log + datetime.timedelta(microseconds=1)
    previous_map[key] = now
    message = "{}::{}---{}--{}\n".format(now.strftime('%Y-%m-%d %H:%M:%S.%f'),
                                         threading.get_ident() + 100000, elapse, s)
    _log.console(message)
    time_log_log.info("{}--{}".format(elapse, s))


def time_err(s):
    time_key(s, str(threading.get_ident()), __error_log)


def time_log(s):
    time_key(s, str(threading.get_ident()), __dual_log)


def restore():
    global __dual_log
    sys.stdout = __dual_log.terminal
    global __error_log
    sys.stderr = __error_log.terminal
