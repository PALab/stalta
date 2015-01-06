'''programstalta.py: sta/lta event detection on a serial data stream

usage: python programstalta.py [options] [datafiles]

options:
    -h             print this
    -v             be more verbose
    -g             called from gui
    -c comport     serial port [com7]
    -s filename    write data stream to a sac file
    -w filename    log to a new file named filename
    -e filename    write event spreadsheet to filename
    -i duration    acquire data for duration seconds and then finish
    -l level       log level [info] of (error, warn, info, debug)
    -m             instantiate Queue logger
    -p             plot results using matplotlib
    -r             show running averages on the plot
    -y             add a trace subplot
    -d             plot histograms
    -q             don't make alarm sounds
    -S tsta        set Tsta
    -L tlta        set Tlta
    -T tthresh     set Triggerthreshold
    -D dtthresh    set Detriggerthreshold
    -F tdesense    set Trigdsensetime
    -P trigdur     set Triggerduration
    -A alarmdur    set Alarmduration

If one or more of the optional arguments, shown as datafiles above,
are present, each argument must be the name of an amaseis data file, a
sac data file, a columnar data file, or a wav data file.  Each of
these files is processed by the program as though it were the input
data stream.  Each is handled separately and the apparent output times
(but not the time in the log header) are adjusted to make the sta/lta
algorithm work properly.

When one or more file arguments are present, the program does not open
the serial port.  Otherwise data are acquired from the comport/serial
port.  The sample rate and data offset are fixed in global module
variables.  (So far we're only dealing with a single data source: the
nerdaq/TC1.)
'''

version = "2.70"
lastchangedate = "2014-12-26"

import sys
import getopt
import time
import math
import os.path

import base
from logger import *
import datainput
import dataoutput
import scanevents
import queuedserialport
import plotevents


# see if winsound is availale and if not fall back on a dummy function

def dummyalarmfcn(a = None, b = None, c = None):
    pass

try:
    from winsound import PlaySound
    from winsound import SND_ASYNC, SND_FILENAME, SND_LOOP
    has_winsound = True
    alarmfcn = PlaySound
except:
    has_winsound = False
    SND_ASYNC = 0
    SND_FILENAME = 0
    SND_LOOP = 0
    alarmfcn = dummyalarmfcn

base.Globs["iswin"] = has_winsound


# default configuration variables

# make sure sound file exists else disable audio
# added default.wav to the source tree

Possiblesoundfiles = (
    "c:/Windows/Media/Alarms/eqalarm.wav",
    "c:/Windows/Media/Alarms/alarm.wav",
    "C:/Windows/Media/notify.wav",
    "default.wav",
)

Soundfile = None
if has_winsound:
    for trialsndfile in Possiblesoundfiles:
        if os.path.exists(trialsndfile):
            Soundfile = trialsndfile
            break
if Soundfile is None:
    alarmfcn = dummyalarmfcn


Comport = "com7"
Samplespersecond = 18.78
Zzero = 32768
Tsta = 0.25
Tlta = 90.0
Triggerthreshold = 4.0
Detriggerthreshold = 2.0
Trigdsensetime = 100.0
Trigduration = 30.0
Alarmduration = 30.0

# import everything from the configstalta module
#
# from configstalta import *
#


def ctime2str(ctime):
    "float time to usable, short string"
    secs, fracs = divmod(ctime, 1.0)
    stt = time.gmtime(ctime)
    strt = "%02d:%02d:%02d.%02d" % (stt.tm_hour, stt.tm_min, stt.tm_sec,
                                    int(100 * fracs))
    return strt



class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv = None):
    if argv is None:
        argv = sys.argv

    global Tsta, Tlta, Triggerthreshold, Detriggerthreshold
    global Trigdsensetime, Trigduration
    global Alarmduration

    options = "vhgw:e:c:s:i:l:mprydqS:L:D:T:A:F:P:"

    logfiles = []
    loglevel = "info"
    comport = Comport
    verbose = 1
    doQueue = False
    doPlot = False
    doPlotavgs = False
    evfile = None
    sacfile = None
    job_duration = None
    isgui = False
    separate_y = False
    doHist = False

    setLogTime(time.gmtime)
    doalarm = True

    try:
        try:
            opts, datafiles = getopt.getopt(argv[1:], options, ["help"])
        except getopt.error, msg:
            raise Usage(msg)

        # process options
        for o, a in opts:
            if o in ("-h", "--help"):
                print __doc__ + "\n\n" + version
                sys.exit(0)
            elif o == "-v":
                verbose += 1
            elif o == "-g":
                isgui = True
            elif o == "-w":
                logfiles.append((a, "wb"))
            elif o == "-e":
                evfile = a
            elif o == "-l":
                loglevel = a
            elif o == "-c":
                comport = a
            elif o == "-s":
                sacfile = a
            elif o == "-i":
                job_duration = float(a)
            elif o == "-m":
                doQueue = True
            elif o == "-p":
                doPlot = True
            elif o == "-r":
                doPlotavgs = True
            elif o == "-y":
                separate_y = True
            elif o == "-d":
                doHist = True
            elif o == "-q":
                doalarm = False
            elif o == "-S":
                Tsta = float(a)
            elif o == "-L":
                Tlta = float(a)
            elif o == "-T":
                Triggerthreshold = float(a)
            elif o == "-D":
                Detriggerthreshold = float(a)
            elif o == "-F":
                Trigdsensetime = float(a)
            elif o == "-P":
                Trigduration = float(a)
            elif o == "-A":
                Alarmduration = float(a)

        configureStream(loglevel, sys.stderr)
        if doQueue:
            configureQueue(loglevel, base.BaseQ)
        for fname, fmode in logfiles:
            configureFile(loglevel, fname, fmode)

        log().critical("start programstalta.py: sta/lta event detection")
        if base.Globs["version"] == "":
            logversion = "local version: " + version
        else:
            logversion = "global version: " + base.Globs["version"]
        log().critical(logversion)

        for fname, fmode in logfiles:
            log().info("logging to: %s  mode: %s" % (fname, fmode))

        datafiles = list(datafiles)
        if len(datafiles) > 0:
            iomode = "virtual"
        else:
            iomode = "real"
            try:
                serial_port = queuedserialport.ThreadedSerialPort(
                    comport,
                    baudrate = 9600,
                    timeout = 2.0,
                    init_skip = 5,
                )
                fbase = comport
                sps = Samplespersecond
                dt = 1.0 / sps
            except:
                log().exception("fatal serial port error on %s" % comport)
                return 4


        # initialize stuff

        log().info("iomode = %s" % iomode)
        if len(datafiles) > 0:
            log().debug("datafiles: %s" % str(datafiles))

        job_starttime = time.time()
        nin = 0  # need this as a startup flag
        dataary = []  # need this is a startup flag

        while True:

            base.Globs["predatacallback"]()
            if base.Globs["quitflag"]:
                return 0

            finishflag = base.Globs["finishflag"]
            if job_duration is not None:
                job_done = (time.time() - job_starttime) >= job_duration
            else:
                job_done = False
            data_done = (iomode == "virtual"
                    and len(dataary) > 0 and nin >= len(dataary))
            any_data = nin > 0

            if any_data and (finishflag or job_done or data_done):
                if iomode == "real":
                    serial_port.close()
                if state == "triggered":
                    trig_duration = vtime - trigtime
                    trig_total += trig_duration
                    log().info("    event %.2f sec   retrig %3d   rmax %.2f"
                               % (trig_duration, retriggers, ratiomax))
                    state = "detriggered"
                    trigs.append((trigtime, vtime, retriggers))
                trig_frac = float(trig_total) \
                               / max(1.0, vtime - starttime)
                log().info("last sample time: %s" % ctime2str(vtime))
                log().info("total:  samples %d   time %.5g sec"
                           % (nin, vtime - starttime))
                log().info("total event time:  %.3g sec (%.2g%%)"
                           % (trig_total, 100.0 * trig_frac))
                if sacfile is not None:
                    log().info("writing data to %s" % sacfile)
                    dataoutput.writesac(sacfile, tary, yary, starttime)
                if evfile is not None and doQueue:
                    log().info("writing events to %s" % evfile)
                    scanevents.scanstream(base.BaseQ, evfile, Tsta,
                                          Tlta, Triggerthreshold,
                                          Detriggerthreshold,
                                          Trigdsensetime, sps)
                if doPlot:
                    log().debug("generating plot(s)")
                    plotevents.eventplot(tary, yary, sary, lary, rary, trigs,
                                         dt, t0, Tsta, Tlta,
                                         Triggerthreshold, Detriggerthreshold,
                                         Trigdsensetime,
                                         fbase, doPlotavgs, doHist, isgui,
                                         separate_y = separate_y)
                if base.Globs["finishflag"] or job_done:
                    return 0

            if iomode == "real":
                try:
                    xstr, vtime = base.SerinQ.get(True, 10.0)
                except:
                    log().exception("SerinQ error")
                    return 1
                sample_val = float(xstr) - Zzero
                if nin == 0:
                    t0 = vtime

            else:
                if nin >= len(dataary):  # proceed to next file, if any
                    if len(datafiles) <= 0:
                        return 0
                    currentfile = datafiles.pop(0)
                    fpath, fbase = os.path.split(currentfile)
                    log().info("file: '%s'" % fbase)
                    log().info("  path: '%s'" % fpath)
                    file_input = datainput.FileScanner(currentfile)
                    dataary, dt, t0, info = file_input['data'][0]
                    log().info("  starttime %s"
                               % time.asctime(time.gmtime(t0)))
                    log().info("  dt: %.3f  sps: %.2f  t0: %.1f"
                               % (dt, 1.0/dt, t0))
                    # recompute the arrays, etc
                    sps = 1.0 / dt
                    nin = 0

                sample_val = float(dataary[nin])
                vtime = t0 + nin*dt

            if nin == 0:
                Nsta = max(2, int(math.ceil(Tsta * sps)))
                Nlta = max(Nsta + 2, int(math.ceil(Tlta * sps)))
                Zsta = Nsta * [0.0]
                Zlta = Nlta * [0.0]
                tary = []
                yary = []
                rary = []
                sary = []
                lary = []
                trigs = []
                fninlta = 0.0
                starttime = t0
                ntrig = 0
                trig_total = 0.0
                state = "detriggered"
                alarmstate = None

                if job_duration is not None:
                    log().info("  timed job duration: %.1f" % job_duration)
                log().info("  Nsta: %d  Nlta: %d" % (Nsta, Nlta))
                log().info("  Tsta: %.1f  Tlta: %.1f  Tthr: %.1f  Dthr: %.1f"
                           % (Tsta, Tlta, Triggerthreshold, Detriggerthreshold))
                log().info("  sps: %.3f  Fdesens: %.1f"
                           % (sps, Trigdsensetime, ))
                log().info("first sample time: %s" % ctime2str(vtime))

            # we use circular data buffers: all that matters is the sum.
            nin += 1
            fninlta += 1.0 if state == "detriggered" \
                       else (1.0 / max(1.0, Trigdsensetime * sps))
            Zsta[nin % Nsta] = abs(sample_val)
            Zlta[int(fninlta) % Nlta] = abs(sample_val)

            ysta = sum(Zsta) / float(Nsta)
            ylta = sum(Zlta) / float(Nlta)
            ratio = ysta / max(1.0 / Nlta, ylta) if nin >= max(Nsta, Nlta) \
                    else 1.0
            tary.append(vtime)
            yary.append(sample_val)
            sary.append(ysta)
            lary.append(ylta)
            rary.append(ratio)

            base.Globs["postdatacallback"]()

            if nin < max(Nlta, Nsta):  # skip tests until the Z* arrays are full
                continue
            if nin == max(Nlta, Nsta):
                log().info("test start  time: %s  sample: %d"
                           % (ctime2str(vtime), nin))

            if state == "detriggered":
                if ratio >= Triggerthreshold:
                    trigtime = vtime
                    lasttrigtime = vtime
                    retriggers = 0
                    ratiomax = ratio
                    ntrig += 1
                    log().info("trigger[%d] at %s" % (ntrig, ctime2str(vtime)))
                    if alarmstate is None and doalarm and iomode == "real":
                        log().debug("alarm sound on at %s" % ctime2str(vtime))
                        alarmfcn(Soundfile,
                                 SND_FILENAME
                                 | SND_LOOP
                                 | SND_ASYNC)
                        alarmstate = vtime + Alarmduration
                    state = "triggered"

            else:  # must be in triggered state
                trig_timeup = vtime >= (lasttrigtime + Trigduration)
                if ratio <= Detriggerthreshold and trig_timeup:
                    trig_duration = vtime - trigtime
                    trig_total += trig_duration
                    trig_frac = float(trig_total) / max(1.0, vtime - starttime)
                    log().info("    event %.2f sec   retrig %3d   rmax %.2f"
                               % (trig_duration, retriggers, ratiomax))
                    state = "detriggered"
                    trigs.append((trigtime, vtime, retriggers))
                elif ratio >= Triggerthreshold:
                    ratiomax = max(ratio, ratiomax)
                    lasttrigtime = vtime
                    retriggers += 1

            if alarmstate is not None:
                if (vtime >= alarmstate) or (state == "detriggered"):
                    if doalarm and iomode == "real":
                        log().debug("alarm sound off at %s" % ctime2str(vtime))
                        alarmfcn(None, SND_ASYNC)
                    alarmstate = None

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use -h"
        return 2

    except Exception, e:
        log().exception("run-time error")
        print >> sys.stderr, e
        return 3


if __name__ == "__main__":
    sys.exit(main())
