'''eventgui.py -- gui for programstalta.py

usage: python eventgui.py [options]

options:
    -h            print this
'''

version = "0.55"
lastchangedate = "2014-12-14"

import sys
import getopt
import posixpath as pp
import pprint

from Tkinter import *
# from ttk import *
import tkFont
import tkFileDialog
import tkMessageBox

import base
from serialports import serialports
from logger import log
from programstalta import main as pgmmain
from programstalta import version as pgmversion


def force_suffix(fname, suffix):
    """won't suffix a directory.
    second argument should not start with a period."""
    head, tail = pp.split(fname)
    if len(tail) == 0:
        return head
    if suffix[0] == ".":
        suffix = suffix[1:]
    fpart, fext = pp.splitext(tail)
    newp = pp.join(head, fpart + "." + suffix)
    return pp.normpath(newp)


class App(Frame):

    def __init__(self, master):

        Frame.__init__(self, master)

        self.master = master
        self.truedatafile = ""
        self.statefile = ""
        self.isrunning = False

        self.entf = tkFont.Font(size = 14)
        self.lblf = tkFont.Font(size = 14)
        self.btnf = tkFont.Font(size = 12, slant = tkFont.ITALIC,
                                weight = tkFont.BOLD)
        self.opnf = tkFont.Font(size = 14)

        self.bgcolor = "#EEEEEE"
        self.master.config(bg = self.bgcolor)

        self.option_add("*background", self.bgcolor)
        self.option_add("*Label*font", self.entf)
        self.option_add("*Entry*font", self.entf)
        self.option_add("*Button*font", self.btnf)
        self.option_add("*OptionMenu*font", self.opnf)

        self.option_add("*Button*background", "#C3C3C3")
        self.option_add("*Checkbutton*background", "#D0D0D0")
        self.option_add("*OptionMenu*background", "#C3C3C3")

        row = 0
        row += 1
        Label(master, text = "processing parameters", font = self.lblf,
              relief = RAISED, width = 30,
              ).grid(row = row, column = 3, columnspan = 2, sticky = E + W)
        Label(master, text = " ").grid(row = row, column = 6, sticky = W,
                                       padx = 50)


        row += 1
        Label(master, text = "Tsta").grid(row = row, column = 3, sticky = E)
        self.Tsta = StringVar()
        self.Tsta.set("0.25")
        Entry(master, width = 10, textvariable = self.Tsta
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "short time average window"
              ).grid(row = row, column = 5, sticky = W)
        Label(master, text = "secs").grid(row = row, column = 6, sticky = W)

        row += 1
        Label(master, text = "Tlta").grid(row = row, column = 3, sticky = E)
        self.Tlta = StringVar()
        self.Tlta.set("90.0")
        Entry(master, width = 10, textvariable = self.Tlta
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "long time average window"
              ).grid(row = row, column = 5, sticky = W)
        Label(master, text = "secs").grid(row = row, column = 6, sticky = W)

        row += 1
        Label(master, text = "Trigger").grid(row = row, column = 3, sticky = E)
        self.Triggerthreshold = StringVar()
        self.Triggerthreshold.set("5.0")
        Entry(master, width = 10, textvariable = self.Triggerthreshold
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "sta/lta trigger level"
              ).grid(row = row, column = 5, sticky = W)
        Label(master, text = "ratio").grid(row = row, column = 6, sticky = W)

        row += 1
        Label(master, text = "Detrigger").grid(row = row,
                                               column = 3, sticky = E)
        self.Detriggerthreshold = StringVar()
        self.Detriggerthreshold.set("2.0")
        Entry(master, width = 10, textvariable = self.Detriggerthreshold
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "sta/lta de-trigger level"
              ).grid(row = row, column = 5, sticky = W)
        Label(master, text = "ratio").grid(row = row, column = 6, sticky = W)

        row += 1
        Label(master, text = "Trigduration"
              ).grid(row = row, column = 3, sticky = E)
        self.Trigduration = StringVar()
        self.Trigduration.set("30.0")
        Entry(master, width = 10, textvariable = self.Trigduration,
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "post-trigger event duration"
              ).grid(row = row, column = 5, sticky = W)
        Label(master, text = "secs").grid(row = row, column = 6, sticky = W)

        row += 1
        Label(master, text = "Trigdesense"
              ).grid(row = row, column = 3, sticky = E)
        self.Trigdsensetime = StringVar()
        self.Trigdsensetime.set("0.0")
        Entry(master, width = 10, textvariable = self.Trigdsensetime,
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "lta desense time scale"
              ).grid(row = row, column = 5, sticky = W)
        Label(master, text = "secs").grid(row = row, column = 6, sticky = W)

        row += 1
        Label(master, text = "  ").grid(row = row, column = 3, sticky = W)

        row += 1
        Label(master, text = "logging parameters", font = self.lblf,
              relief = RAISED, width = 30,
              ).grid(row = row, column = 3, columnspan = 2, sticky = E + W)

        row += 1
        Label(master, text = "Loglevel"
              ).grid(row = row, column = 3, sticky = E)
        self.Loglevelsel = StringVar()
        self.Loglevelsel.set("debug")
        self.llb = OptionMenu(master, self.Loglevelsel,
                              "debug", "info", "warning", "error")
        self.llb.grid(row = row, column = 4, sticky = W)
        Label(master, text = "logging level"
              ).grid(row = row, column = 5, sticky = W)


        row += 1
        Label(master, text = "Logfile"
              ).grid(row = row, column = 3, sticky = E)
        self.Logfile = StringVar()
        self.Logfile.set("")
        Entry(master, width = 10, textvariable = self.Logfile
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "log (txt) filename"
              ).grid(row = row, column = 5, sticky = W)

        row += 1
        self.Outfile = StringVar()
        self.Outfile.set("")
        self.Outshowfile = StringVar()
        self.Outshowfile.set("")
        Entry(master, width = 10, textvariable = self.Outshowfile
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "data (sac) filename"
              ).grid(row = row, column = 5, sticky = W)
        Button(master, text = "specify output file", command = self.OnOutBrowse,
               ).grid(row = row, column = 3, sticky = E + W, padx = 4)

        row += 1
        Label(master, text = "Eventfile"
              ).grid(row = row, column = 3, sticky = E)
        self.Eventfile = StringVar()
        self.Eventfile.set("")
        Entry(master, width = 10, textvariable = self.Eventfile
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "event (xlsx) filename"
              ).grid(row = row, column = 5, sticky = W)

        row += 1
        Label(master, text = "  ").grid(row = row, column = 3, sticky = W)

        row += 1
        Label(master, text = "control parameters", font = self.lblf,
              relief = RAISED, width = 30,
              ).grid(row = row, column = 3, columnspan = 2, sticky = E + W)

        row += 1
        Label(master, text = "Jobduration"
              ).grid(row = row, column = 3, sticky = E)
        self.Jobduration = StringVar()
        self.Jobduration.set("")
        Entry(master, width = 10, textvariable = self.Jobduration
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "acquisition duration"
              ).grid(row = row, column = 5, sticky = W)
        Label(master, text = "secs").grid(row = row, column = 6, sticky = W)

        row += 1
        self.Doalarm = IntVar()
        Checkbutton(master, text = "event alarm", variable = self.Doalarm,
                    font = self.entf).grid(row = row, column = 3, sticky = W)
        self.Alarmduration = StringVar()
        self.Alarmduration.set("2.0")
        Entry(master, width = 10, textvariable = self.Alarmduration
              ).grid(row = row, column = 4, sticky = W)
        Label(master, text = "alarm duration"
              ).grid(row = row, column = 5, sticky = W)
        Label(master, text = "secs").grid(row = row, column = 6, sticky = W)

        row += 1
        Label(master, text = "  ").grid(row = row, column = 3, sticky = W)

        row += 1
        Label(master, text = "data source", font = self.lblf,
              relief = RAISED, width = 30,
              ).grid(row = row, column = 3, columnspan = 2, sticky = E + W)


        row += 1
        self.Comcheck = IntVar()
        Checkbutton(master, text = "use comport", variable = self.Comcheck,
                    font = self.entf,
                    ).grid(row = row, column = 3, sticky = W)
        comportlist = []
        for name, desc, hwid in serialports():
            comportlist.append(name)
        if len(comportlist) == 0:
            comportlist = ["-none-", ]
        self.comport = StringVar()
        self.comport.set(comportlist[0])
        self.ports = OptionMenu(master, self.comport, *comportlist)
        self.ports.grid(row = row, column = 4, sticky = W)
        Label(master, text = "active comport"
              ).grid(row = row, column = 5, sticky = W)

        row += 1
        self.datafile = StringVar()
        self.datafile.set("")
        self.truedatafile = StringVar()
        self.truedatafile.set("")
        Label(master, text = "input (sac) file"
              ).grid(row = row, column = 5, sticky = W)
        Entry(master, textvariable = self.datafile,
              ).grid(row = row, column = 4, sticky = W)
        Button(master, text = "select input file", command = self.OnBrowse,
               ).grid(row = row, column = 3, sticky = E + W, padx = 4)


        row += 1
        Label(master, text = "  ").grid(row = row, column = 3, sticky = W)

        row += 1
        Label(master, text = "display control", font = self.lblf,
              relief = RAISED, width = 30,
              ).grid(row = row, column = 3, columnspan = 2, sticky = E + W)


        row += 1
        self.doplot = IntVar()
        Checkbutton(master, text = "plot results", variable = self.doplot,
                    font = self.entf,
                    ).grid(row = row, column = 3, columnspan = 2, sticky = W)

        row += 1
        self.doplotavg = IntVar()
        Checkbutton(master, text = "also plot running averages",
                    variable = self.doplotavg,
                    font = self.entf,
                    ).grid(row = row, column = 3, columnspan = 2, sticky = W,
                           padx = 20)

        row += 1
        self.doploty = IntVar()
        Checkbutton(master, text = "show trace subplot",
                    variable = self.doploty,
                    font = self.entf,
                    ).grid(row = row, column = 3, columnspan = 2, sticky = W,
                           padx = 20)

        row += 1
        self.doploth = IntVar()
        Checkbutton(master, text = "plot histograms",
                    variable = self.doploth,
                    font = self.entf,
                    ).grid(row = row, column = 3, columnspan = 2, sticky = W,
                           padx = 20)

        row += 1
        self.showcommand = IntVar()
        Checkbutton(master, text = "show command line (debug)",
                    variable = self.showcommand,
                    font = self.entf,
                    ).grid(row = row, column = 3, columnspan = 2, sticky = W)

        row += 1
        Label(master, text = "  ").grid(row = row, column = 3, sticky = W)

        row += 1
        col = 3
        self.runb = Button(master, fg = "blue", text = "run",
               command = self.OnRun)
        self.runb.grid(row = row, column = col, sticky = N)
        col += 1
        self.finishb = Button(master, fg = "magenta", text = "finish",
                              state = DISABLED,
                              command = self.OnFinish)
        self.finishb.grid(row = row, column = col, sticky = N)
        col += 1
        Button(master, fg = "blue", text = "save", state = DISABLED,
               command = self.saveState).grid(row = row,
                                              column = col, sticky = N)
        col += 1
        Button(master, fg = "blue", text = "load", state = DISABLED,
               command = self.loadState).grid(row = row,
                                              column = col, sticky = W)
        col += 1
        Button(master, fg = "red", text = "quit",
               command = self.OnQuit).grid(row = row, column = col, sticky = N)
        col += 1
        Label(master, fg = "red", text = "      ",
              ).grid(row = row, column = col, sticky = W)


    def OnRun(self):
        args = [
            "eventgui",
            "-g",
            "-S", self.Tsta.get(),
            "-L", self.Tlta.get(),
            "-T", self.Triggerthreshold.get(),
            "-D", self.Detriggerthreshold.get(),
            "-P", self.Trigduration.get(),
            "-F", self.Trigdsensetime.get(),
            "-A", self.Alarmduration.get(),
            "-l", self.Loglevelsel.get(),
            "-m",
        ]
        if self.Logfile.get() != "":
            args.extend(("-w", force_suffix(self.Logfile.get(), "txt")))
        if self.Outfile.get() != "":
            args.extend(("-s", force_suffix(self.Outfile.get(), "sac")))
        elif self.Outshowfile.get() != "":
            args.extend(("-s", force_suffix(self.Outshowfile.get(), "sac")))
        if self.Eventfile.get() != "":
            args.extend(("-e", force_suffix(self.Eventfile.get(), "xlsx")))
        if (self.doplot.get() or self.doplotavg.get()
              or self.doploty.get() or self.doploth.get()):
            args.append("-p")
            if self.doplotavg.get():
                args.append("-r")
            if self.doploty.get():
                args.append("-y")
            if self.doploth.get():
                args.append("-d")
        if not self.Doalarm.get():
            args.append("-q")
        if self.Comcheck.get() == 0:
            args.append("-q")
            if self.truedatafile.get() != "":
                args.append(self.truedatafile.get())
            elif self.datafile.get() != "":
                args.append(self.datafile.get())
            else:
                tkMessageBox.showerror(title = "no data source",
                    message = "check 'use comport' or provide a data file")
                return
        else:
            if self.comport.get() != "-none-":
                args.extend(("-c", self.comport.get()))
                if self.Jobduration.get() != "":
                    args.extend(("-i", self.Jobduration.get()))
            else:
                tkMessageBox.showerror(title = "no available serial port",
                    message = "you must choose a data file")
                self.Comcheck.set(0)
                return
        if self.showcommand.get():
            print >> sys.stderr, "--------command line-----------"
            pprint.pprint(args, stream = sys.stderr)
            print >> sys.stderr, "-------------------------------"
        base.Globs["quitflag"] = False
        base.Globs["finishflag"] = False
        self.runb.config(state = DISABLED)
        self.finishb.config(state = NORMAL)
        self.isrunning = True
        r = pgmmain(args)
        self.isrunning = False
        self.finishb.config(state = DISABLED)
        self.runb.config(state = NORMAL)
        if r != 0:
            log().error("pgmmain returned %s" % r)
            self.reallyquit()
        if base.Globs["quitflag"]:
            log().debug("quitting on global quitflag")
            self.reallyquit()
        base.Globs["quitflag"] = True
        base.Globs["finishflag"] = True


    def OnOutBrowse(self):
        self.Outfile.set(tkFileDialog.asksaveasfilename(
            filetypes = [('sac data file', '*.sac')]))
        if self.Outfile.get() != "":
            self.Outshowfile.set(pp.basename(self.Outfile.get()))


    def OnBrowse(self):
        self.truedatafile.set(tkFileDialog.askopenfilename())
        if self.truedatafile.get() != "":
            self.datafile.set(pp.basename(self.truedatafile.get()))


    def loadState(self):
        pass


    def saveState(self):
        pass


    def reallyquit(self):
        self.quit()


    def OnFinish(self):
        base.Globs["finishflag"] = True


    def OnQuit(self):
        if not self.isrunning:
            self.reallyquit()
        if base.Globs["quitflag"]:
            self.reallyquit()
        base.Globs["quitflag"] = True



def main(argv=None):
    if argv is None:
        argv = sys.argv

    options = "h"

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

        root = Tk()
        app = App(root)

        base.Globs["predatacallback"] = app.update
        base.Globs["version"] = "%.2f" % (float(version) + float(pgmversion))
        app.master.title("sta/lta event detection"
                         + "           version " + base.Globs["version"]
                         + "              "
                         + "   [gui " + version
                         + "   algorithm " + pgmversion + "]")
        app.mainloop()
        try:
            root.destroy()
        except:
            pass

    except Exception, e:
        log().exception("gui error")
        print >> sys.stderr, e
        return 3


if __name__ == "__main__":
    sys.exit(main())
