'''logger for pysep'''

import sys
import time
import logging
import logging.handlers as handlers

import base

__activelogger = None

__logname = "stalta"

_logformat = "%(levelname)s %(asctime)s:  %(message)s"

__logfilename = "stalta.log"

__logfilemode = "wb"

__logfilelimit = 8 * 2**22  # 32 MiB

__logfilecount = 9

__levels = (("critical", logging.CRITICAL),
            ("error", logging.ERROR),
            ("warning", logging.WARN),
            ("info", logging.INFO),
            ("debug", logging.DEBUG),
            )

__defaultlevel = logging.WARN


#
# controls time used in logging preamble.  alternative is time.gmtime
#
def setLogTime(converter = time.localtime):
    logging.Formatter.converter = converter


def _loglevel(level):
    for name, l in __levels:
        if level.lower() == name.lower():
            return l
    return __defaultlevel


def log():
    global __activelogger
    if __activelogger is None:
        __activelogger = logging.getLogger(__logname)
        logging.captureWarnings(True)  # not sure this is useful
    return __activelogger


def configureRotater(level, rollover = True):
    log().setLevel(_loglevel(level))
    log().propagate = False
    rothandler = handlers.RotatingFileHandler(filename = __logfilename,
                                              mode = __logfilemode,
                                              maxBytes = __logfilelimit,
                                              backupCount = __logfilecount)
    formatter = logging.Formatter(_logformat)
    rothandler.setFormatter(formatter)
    log().addHandler(rothandler)
    if rollover:
        rothandler.doRollover()


__active_file_handlers = []
        

def configureFile(level, filename, mode = "wb"):

    global __active_file_handlers
    for a, fn, fm in __active_file_handlers:
        a.close()
        log().removeHandler(a)
    __active_file_handlers = []

    log().setLevel(_loglevel(level))
    log().propagate = False
    filehandler = logging.FileHandler(filename, mode)
    formatter = logging.Formatter(_logformat)
    filehandler.setFormatter(formatter)
    log().addHandler(filehandler)
    __active_file_handlers.append((filehandler, filename, mode))


__active_streams = []


def configureStream(level, stream = None):

    global __active_streams
    if stream in __active_streams:
        return
    __active_streams.append(stream)

    log().setLevel(_loglevel(level))
    log().propagate = False
    if stream is None:
        stream = sys.stderr
    streamhandler = logging.StreamHandler(stream = stream)
    formatter = logging.Formatter(_logformat)
    streamhandler.setFormatter(formatter)
    log().addHandler(streamhandler)


class LogQueueHandler(logging.Handler):

    def __init__(self, level = logging.ERROR, queue = base.BaseQ):
        logging.Handler.__init__(self)
        self.Q = queue
        self.setLevel(_loglevel(level))
        self.setFormatter(logging.Formatter(_logformat))

    def emit(self, record):
        s = self.format(record)
        # print "rec: " + s
        self.Q.put(s)


__active_Queues = []


def configureQueue(level, queue = base.BaseQ):

    global __active_Queues
    if queue in __active_Queues:
        return
    __active_Queues.append(queue)

    queuehandler = LogQueueHandler(level, queue)
    log().addHandler(queuehandler)



















