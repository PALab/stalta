#!/usr/bin/env python
"""
read an amaseis 1-hour datafile
"""
import sys, os, time, getopt
import string, re
import struct
import traceback
import math
import csv, gzip

import numpy as np
from logger import log


def readamaseisdata(inp):
    '''
    Slurps a one-hour amaseis file and returns an array of one Pulse
    '''
    try:
        npts = struct.unpack("L", inp.read(4))[0]
        rest = inp.read()
        nvals = len(rest)/2
        ary = struct.unpack("%dh" % nvals, rest)
        ary = list(ary[0:npts])
        if len(ary) > npts:
            log().warning("%s: from %d to %d" % ('amaseis', nvals, len(ary)))
        elif len(ary) < npts:
            log().warning("%s: only %d of %d" % ('amaseis', len(ary), npts))
        inp.close()
    except Exception, e:
        log().error("readamaseis: " + str(e))
        return None

    info = "amaseis with %d of %d valid" % (nvals, npts)
    dt = 3600.0 / npts
    t0 = 0.0
    return [ary, dt, t0, info]










