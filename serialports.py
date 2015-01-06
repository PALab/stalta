'''serialports.serialports() returns a list of available serial ports.
Each entry consists of (name, description, hardware_id).  Optional
argument is a regular expression used to filter the ports returned.

'''

import sys
import re
import serial.tools.list_ports as stlp


def serialports(regexp = None):

    if regexp is not None:
        rec = re.compile(regexp, re.I)  # ignore case
    for name, desc, hwid in stlp.comports():
        if regexp is None or rec.search(name) or rec.search(desc) \
           or rec.search(hwid):
            yield name, desc, hwid



class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):

    import getopt

    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
        except getopt.error, msg:
            raise Usage(msg)

        # process options
        for o, a in opts:
            if o in ("-h", "--help"):
                print __doc__
                sys.exit(0)

        filter = None if len(args) == 0 else args[0]
        for name, desc, hwid in serialports(filter):
            print "  %-5s  %s  %s" % (name, desc, hwid)

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())

