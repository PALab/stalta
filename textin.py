#!/usr/bin/env python
"""
functions to read text data of various types.
"""

__docformat__ = "restructuredtext en"


import sys, os, time, getopt
import string, re
import traceback
import math
import csv, gzip

import numpy as np
import numpy.linalg as linalg

from logger import log


def readcoldata(source, No_x = 0):
    '''
    Scans an input source, a file-like object, and looks for

        - an optional info block of lines, each starting with a
          non-numeric character (such as\'#\').
        - one or more data blocks, each of lines of the form

                [optional x column]<sep>y0[<sep>yn]*

            where <sep> is one or more characters from \',\'
            \';\', \' \', \'\t\'.
            -- if there are more than one column and the first column
               is not monotonic, it will be assumed to be y0.
            -- if there are multiple y columns and NO x column and the
               first column may be monotonic, you must set No_x = 1.

          Data blocks are separated by an info group starting with
          a non-numeric character.  (Xmgrace uses & between sets.)

    Returns None if the source format is inconsistent with the above
    or a list of (ary, dt, t0, infoblock).
    '''

    leading_numeric = ['-', '+', '.', '0', '1', '2', '3', '4', '5',
                       '6', '7', '8', '9']
    ttable = string.maketrans("\t,:", "   ")

    state = 'info'
    datablocks = []
    info = []
    thisblock = []

    for l in source:
        l = l.strip()
        if len(l) == 0:
            continue
        for s in l:
            if s not in string.printable:
                return None
        notanum = l[0] not in leading_numeric

        if state == 'info' and notanum:
            info.append(l)
            continue

        state = 'data'

        if notanum:
            if len(thisblock) > 0:
                datablocks.append((thisblock, info))
                thisblock = []
                info = []
                state = 'info'
                continue
            else:
                return None

        thisblock.append([float(f) for f in l.translate(ttable).split()])

    if len(thisblock) > 0:
        datablocks.append((thisblock, info))

    log().debug("source has %d datablocks", len(datablocks))

    retlist = []
    blockno = 0
    for db, inf in datablocks:
        dbary = np.array(db)
        log().debug("datablock %d has shape %s", blockno, dbary.shape)
        if dbary.shape[1] > 1 and not No_x and ismonotonic(dbary[:,0]):
            t0, dt = sampleparams(dbary[:,0])
            dbary = dbary[:,1:]
        else:
            t0, dt = (0.0, 1.0)
        if len(inf) == 0:
            inf = None
        for colidx in range(dbary.shape[1]):
            retlist.append((dbary[:,colidx], dt, t0, inf[0]))
        blockno += 1

    return retlist


def ismonotonic(t):
    '''true if t is an array and is monotonic'''
    try:
        dt = t[1:] - t[0:-1]
        if dt.min() < 0.0:
            return 0
        return 1
    except:
        return 0


def sampleparams(t):
    '''infer t0, dt from the sample times in t
    '''
    A = np.array([np.ones(len(t)), np.arange(len(t))])
    if 0:
        print >> sys.stderr, (A.shape, t.shape)
        print >> sys.stderr, linalg.lstsq(A.transpose(), t)[0:2]
        print >> sys.stderr, t
        print >> sys.stderr, A
    t0, dt = linalg.lstsq(A.transpose(), t)[0]
    t0 = t[0]
    return t0, dt

