#!/usr/bin/env python
"""
input pulse data ifrom a variety of auto-detected formats

python datainput.py [options]
    options are
        -v          increase verbosity
        -l level    log level name [info]
"""
__docformat__ = "restructuredtext en"

import sys
import time
import getopt
import traceback
import gzip
import zipfile

import numpy as np
import scipy.io.wavfile as wav

from logger import *
import textin
import obspy.core
import amaseisin


def __readwavefile(filein, firstsample = 0, maxsamples = -1):
    '''return a dictionary of the Pulses in the wav file/stream filein
    or None'''

    samplerate, data = wav.read(filein)
    nsamples = len(data)

    firstsample = min(nsamples - 1, firstsample)
    if maxsamples < 0:
        maxsamples = nsamples
    #  samplesin = min(nsamples - firstsample, maxsamples)

    nch = 1

    r = []
    for chno in range(nch):
        r.append([data[firstsample:maxsamples],
                  1.0 / samplerate,
                  firstsample / samplerate,
                  "wav %d" % (chno,)]
                 )
    return r


def __openmaybezip(filename):
    '''see if data file requires gzip or zipfile'''

    try:
        inf = gzip.open(filename)
        inf.readline()
        inf.seek(0)
    except:
        try:
            inf.close()
        except:
            pass
        try:
            zfile = zipfile.ZipFile(filename, "r")
            inf = zfile.open(zfile.namelist()[0], "rU")
            log().debug("%s is a gzip file", filename)
        except:
            try:
                zfile.close()
            except:
                pass
            inf = file(filename, 'rb')
            log().debug("%s is not a gzip file", filename)
    return inf


class BadFileFormat(Exception):
    def __init__(self, msg):
        self.msg = msg


filecount = 0


def FileScanner(filename, fsize = False):

    global filecount

    '''Tries to extract the time series in filename.  Tries sac,
    possibly-zipped wav, possibly-zipped columnar data, and
    possibly-zipped amaseis file.

    On success returns a dictionary containing the keys filename,
    format, and data, a list of the items found as (ary, dt, t0,
    info).  The data list may be empty.

    On failure raises BadFileFormat.
    
    fsize = False disables comparison of physical size and expected
    size for sac files.  Why does this option even exist?
    '''

    log().debug("scanning '%s'", filename)

    pulses = None
    detailary = []
    summaryary = []

    try:
        log().debug("try obspy (sac) trace")
        sacdb = obspy.core.read(filename, fsize = fsize)
        dataformat = "obspy"
        pulses = []
        i = 0
        for tr in sacdb:
            pulses.append((tr.data,
                          1.0 / tr.stats.sampling_rate,
                          tr.stats.starttime.timestamp,
                          str(tr))
                          )
            sacd = None
            details = []
            summaryary.append(str(tr))
            for k in tr.stats.iterkeys():
                if k == 'sac':
                    sacd = tr.stats[k]
                else:
                    details.append("%20s: %s" % (k, tr.stats[k]))
            if sacd is not None:
                kl = sacd.keys()
                kl.sort()
                for k in kl:
                    try:
                        v = int(round(float(sacd[k])))
                        if v == -12345 and verbose == 0:
                            continue
                    except:
                        pass
                    details.append("sacd:: %22s: %s" % (k, sacd[k]))
            detailary.append(details)
            i += 1
    except Exception, e:
        print e
        pulses = None


    if pulses is None:
        inf = __openmaybezip(filename)
        try:
            log().debug("try wav trace")
            pulses = __readwavefile(inf)
            dataformat = "wav"
        except:
            pulses = None
        inf.close()

    if pulses is None:
        inf = __openmaybezip(filename)
        try:
            log().debug("try columnar data trace")
            pulses = textin.readcoldata(inf)
            dataformat = "col"
        except Exception, e:
            print e
            pulses = None
        inf.close()

    if pulses is None:
        try:
            log().debug("try amaseis trace")
            inf = __openmaybezip(filename)
            ary, dt, t0, info = amaseisin.readamaseisdata(inf)
            pulses = [[ary, dt, t0, info]]
            dataformat = "ama"
        except Exception, e:
            r = "error: %s" \
                % traceback.format_exception(sys.exc_type,
                                             sys.exc_value,
                                             sys.exc_traceback)
            log().error(r)
            pulses = None

    if pulses is None:
        raise BadFileFormat("FileScanner failed")

    filecount += 1
    log().debug("success")
    return {'filename': filename,
            'format': dataformat,
            'data': pulses,
            'filecount': filecount
            }



if __name__ == "__main__":

    import glob

    def main(argv = None):

        verbose = 0
        loglevel = "info"
        options = "vl:"

        if argv is None:
            argv = sys.argv
        try:
            opts, args = getopt.getopt(argv[1:], options, ["help"])
        except getopt.error, msg:
            raise RuntimeError(msg)

        for opt, v in opts:
            if opt == "-v":
                verbose += 1
            elif opt == "-l":
                loglevel = v
            elif opt == "-h":
                print >> sys.stderr, __doc__
                return 0

            else:
                print >> sys.stderr, "unknown option: %s %s\n" \
                    % (str(opt), str(v))
                print >> sys.stderr, __doc__
                return 3

        setLogTime(time.gmtime)
        configureStream(loglevel, sys.stderr)
        configureFile(loglevel, "LogFiles/short.log", "wb")
        configureFile(loglevel, "LogFiles/long.log", "ab")

        testfiles = glob.glob("DataFiles/*")
        testfiles.sort()
        testfiles = args

        for testfile in testfiles:
            log().debug("scanning datafile '%s'", testfile)
            pulses = FileScanner(testfile)
            log().info("   '%s' as '%s' yielded %d pulse(s)",
                       pulses['filename'],
                       pulses['format'], len(pulses['data']))
            for ary, dt, t0, info in pulses['data']:
                log().info("    %4d samples  t0 = %10.3e  dt = %10.3e",
                            len(ary), t0, dt)
                log().info("    %10.3e mean  %10.3e sigma  %s",
                            np.mean(ary), np.std(ary), info)
        return 0



    try:
        r = main()
        if r != 0:
            log().error("Exit code %s", r)
    except Exception, e:
        r = "error: %s" \
            % traceback.format_exception(sys.exc_type,
                                         sys.exc_value,
                                         sys.exc_traceback)
        log().error(r)

    sys.stdout.flush()




