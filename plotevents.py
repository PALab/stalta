'''plot event info'''

import base
import datetime
import numpy as np
import matplotlib
if not base.Globs["iswin"]:
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from logger import *



def eventplot(tin, y, sta, lta, ratio, trigs,
              dt, t0, tsta, tlta, trig, detrig, desense,
              filenamebase,
              plotavgs = True, plothist = True,
              isgui = False, separate_y = False):

    y = np.array(y)
    dtime = [datetime.datetime.utcfromtimestamp(x) for x in tin]
    dtmin = dtime[0]
    dtmax = dtime[-1]

    yabs = np.abs(y)
    yabsmax = max(yabs)

    sta = np.array(sta)
    lta = np.array(lta)
    ratio = np.array(ratio)
    pmax = max(sta.max(), lta.max())
    rmax = max(ratio.max(), trig, detrig)

    plt.figure()
    otherax = plt.subplot(211 if separate_y else 111)
    plt.title(("%s   %d events" + "\n"
        + "Tsta: %.3g  Tlta: %.3g  Trig: %.3g  Detrig: %.2g  Tdsense: %.3g")
        % (filenamebase, len(trigs), tsta, tlta, trig, detrig, desense))
    plt.ylabel("ratio")

    if plotavgs:
        plt.plot(dtime, rmax*lta/pmax, color = "orange", label = "lta")
        plt.plot(dtime, rmax*sta/pmax, color = "green", label = "sta")
    plt.plot(dtime, ratio, color = "red", label = "ratio")
    plt.plot((dtmin, dtmax), (trig, trig), "k--")
    plt.plot((dtmin, dtmax), (detrig, detrig), "k--")
    if not separate_y:
        plt.plot(dtime, 0.5 * rmax * yabs / yabsmax, color = "0.4",
                 label = "_ignore", alpha = 0.8)
    plt.legend()
    for tl, tr, retrigs in trigs:
        tl, tr = [datetime.datetime.utcfromtimestamp(x) for x in (tl, tr)]
        xpoly = (tl, tr, tr, tl)
        ypoly = (rmax, rmax, 0.0, 0.0)
        plt.fill(xpoly, ypoly, color = "0.6", alpha = 0.5)

    if separate_y:
        plt.subplot(212, sharex = otherax)
        plt.plot(dtime, y, color = "black")
        ymax = max(y)
        ymin = min(y)
        for tl, tr, retrigs in trigs:
            tl, tr = [datetime.datetime.utcfromtimestamp(x) for x in (tl, tr)]
            xpoly = (tl, tr, tr, tl)
            ypoly = (ymax, ymax, ymin, ymin)
            plt.fill(xpoly, ypoly, color = "0.6", alpha = 0.5)

    fmtr = matplotlib.dates.DateFormatter("%H:%M:%S")
    plt.gca().xaxis.set_major_formatter(fmtr)
    plt.gcf().autofmt_xdate()

    plt.show(block = False if isgui else True)


    if not plothist:
        return

    plt.figure()
    plt.subplot(211)
    plt.title(("%s   %d events" + "\n"
        + "Tsta: %.3g  Tlta: %.3g  Trig: %.3g  Detrig: %.2g  Tdsense: %.3g")
        % (filenamebase, len(trigs), tsta, tlta, trig, detrig, desense))
    plt.hist(lta, bins = 100, normed = True, log = True, color = "black",
             label = "lta")
    plt.hist(sta, bins = 100, normed = True, log = True,
             alpha = 0.5, color = "green", label = "sta")
    plt.legend()
    plt.subplot(212)
    plt.hist(ratio, bins = 100, normed = True, log = True,
             alpha = 0.5, color = "red", label = "ratio")
    plt.legend()

    plt.show(block = False if isgui else True)
