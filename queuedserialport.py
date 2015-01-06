'''serial port in a separate thread feeding a Queue'''

import time
import threading
import serial

from logger import log
import base


class ThreadedSerialPort(threading.Thread):
    def __init__(self,
                 ttynameorfile,
                 baudrate = 9600,
                 timeout = 1.0,
                 init_skip = 0,
                 ):
        threading.Thread.__init__(self)
        log().debug("initializing ThreadedSerialPort")
        self.ttynameorfile = ttynameorfile
        self.baudrate = baudrate
        self.timeout = timeout
        self.init_skip = init_skip
        self.opened = True
        try:
            self.tty = serial.Serial(port = self.ttynameorfile,
                                     timeout = self.timeout,
                                     baudrate = self.baudrate,
                                     bytesize = serial.EIGHTBITS,
                                     parity = serial.PARITY_NONE,
                                     stopbits = serial.STOPBITS_ONE,
                                     )
            log().debug("opened serial port: %s" % self.tty.name)
        except:
            log().exception("serial port open failure")
            base.Globs["quitflag"] = True
            raise
        self.setDaemon(1)
        self.start()


    def close(self):
        self.opened = False
        log().debug("closing serial port")
        self.tty.close()


    def run(self):
        '''serial input may consist of multiple space-separated fields.  only
           use the first one.
        '''
        log().debug("serial infinite loop begin")
        qrange = 0
        queue_warning_threshold = 200
        nin = 0
        while True:
            try:
                if not self.opened:
                    log().debug("serial thread exiting on closed port")
                    return 0
                vtime = time.time()
                str_in = self.tty.readline().strip()
                if str_in == "":
                    return 0
                try:
                    str_out = str_in.split()[0]
                except:
                    log().exception("snag in serial input split")
                    return 0
                nin += 1
                if nin <= self.init_skip:  # skip some initial values
                    continue
            except:
                log().exception("serial port readline failed")
                base.Globs["quitflag"] = True
                return 1
            base.SerinQ.put((str_out, vtime))
            qsize = base.SerinQ.qsize()
            cqrange = int(qsize / 10.0)
            if cqrange != qrange:
                if qsize >= queue_warning_threshold:
                    log().warning("SerinQ size %d exceeds threshold (%d)"
                                  % (qsize, queue_warning_threshold))
                else:
                    log().debug("SerinQ size %d" % qsize)
            qrange = cqrange
