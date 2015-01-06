"""write dataset to a sac file"""

import numpy as np
import obspy.core as ocore


def writesac(sacfile, tary, yary, starttime):

    npts = len(yary)
    if npts < 2:
        dt = 1.0
    else:
        dt = (tary[-1] - tary[0]) / (npts - 1)

    st = ocore.Stats()
    st.npts = npts
    st.delta = dt
    st.starttime = ocore.UTCDateTime(starttime)

    tr = ocore.trace.Trace(data = np.array(yary, dtype = np.dtype(float)),
                           header = st)
    tr.write(sacfile, format = "SAC")

    return npts
