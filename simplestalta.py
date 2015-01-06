'''simplestalta.py: sta/lta event detection on a serial data stream
    version: 1.13
    last change: 2014-11-08
'''
import sys
import time
import math
import serial
import winsound

# default configuration variables

Soundfile = "c:/Windows/Media/Alarms/divehorn.wav"
Comport = "com7"
Samplespersecond = 18.78
Zzero = 32768
Tsta = 2.0
Tlta = 30.0
Triggerthreshold = 4.0
Detriggerthreshold = 2.0
Alarmduration = 30.0

# import everything from the configstalta module

from configstalta import *

# computed quantities

Nsta = int(math.ceil(Tsta * Samplespersecond))
Nlta = int(math.ceil(Tlta * Samplespersecond))

# lists to store the windowed data

Zsta = [0.0 for i in range(Nsta)]
Zlta = [0.0 for i in range(Nlta)]

# initialize stuff

print >> sys.stderr, "\n" +  __doc__
nin = 0
state = "detriggered"
alarmstate = None

try:
    datain = serial.Serial(Comport, 9600)
except:
    print >> sys.stderr, "fatal error: serial open failed for %s" % Comport
    sys.exit(0)

while True:

    xstr = datain.readline().strip()
    if len(xstr) == 0:
        continue

    x = float(abs(int(xstr) - Zzero))
    nin = nin + 1

    # we store values in a cyclic fashion.  all that matters is the sum.
    Zsta[nin % Nsta] = x
    Zlta[nin % Nlta] = x

    if nin < Nlta: # skip tests until the longer array is full
        continue

    if nin == Nlta:
        print >> sys.stderr, "\nbegin ratio testing at %s UTC\n" \
            % time.asctime(time.gmtime())

    ratio = (sum(Zsta) / Nsta) / max(1.0, (sum(Zlta) / Nlta))

    if state == "detriggered":
        if ratio >= Triggerthreshold:
            print >> sys.stderr, "trigger at %s UTC" \
                % time.asctime(time.gmtime())
            trigtime = time.time()
            if alarmstate is None:
                winsound.PlaySound(Soundfile,
                                   winsound.SND_FILENAME
                                   | winsound.SND_LOOP
                                   | winsound.SND_ASYNC)
            alarmstate = time.time() + Alarmduration
            state = "triggered"

    else: # must be in triggered state
        if ratio <= Detriggerthreshold:
            duration = time.time() - trigtime
            print >> sys.stderr, "        lasted %.3f seconds" % duration
            state = "detriggered"

    if alarmstate is not None:
        if (time.time() >= alarmstate) or (state == "detriggered"):
            winsound.PlaySound(None, winsound.SND_ASYNC)
            alarmstate = None
