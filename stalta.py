'''eventgui.py -- gui for programstalta.py

usage: python eventgui.py [options]

options:
    -h            print this
    -t ttktheme   use theme ttktheme [alt]
    -l            list available themes and exit
'''

version = "1.10"
lastchangedate = "2014-12-26"

import sys
import getopt
import posixpath as pp
import pprint

from Tkinter import *
import ttk
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


class App(object):

    def __init__(self, theme):

        self.root = Tk()
        master = ttk.Frame(self.root)
        self.frame = master
        master.pack(expand=True, fill='both')

        deff = tkFont.Font(size = 14, weight = tkFont.BOLD)
        hedf = tkFont.Font(size = 16, weight = tkFont.BOLD)
        entf = tkFont.Font(size = 14, slant = tkFont.ITALIC,
                           weight = tkFont.BOLD)
        lblf = tkFont.Font(size = 12, weight = tkFont.BOLD)
        btnf = tkFont.Font(size = 12, slant = tkFont.ITALIC,
                           weight = tkFont.BOLD)
        abtnf = tkFont.Font(size = 14, weight = tkFont.BOLD)
        opnf = tkFont.Font(size = 14, slant = tkFont.ITALIC)
        ckbf = tkFont.Font(size = 12, weight = tkFont.BOLD)

        lblfg = "darkblue"
        hlblfg = "#60232E"
        vlblfg = "darkblue"
        ulblfg = "#45232E"
        btnfg = "#45442E"
        qbtnfg = "#bb232E"
        entbg = "lightgray"
        entfg = "darkblue"
        ckbfg = "blue"

        sty = ttk.Style()
        sty.theme_use(theme)
        sty.configure('.',
                      font = deff)
        sty.configure("head.TLabel",
                      font = hedf,
                      foreground = hlblfg,
                      relief = RAISED,
                      width = 30,
                      sticky = "w")
        sty.configure("TLabel",
                      font = lblf,
                      foreground = lblfg,
                      sticky = "w")
        sty.configure("var.TLabel",
                      font = lblf,
                      foreground = vlblfg,
                      sticky = "e")
        sty.configure("unit.TLabel",
                      font = lblf,
                      foreground = ulblfg,
                      sticky = W)
        sty.configure("TButton",
                      font = btnf,
                      foreground = btnfg,
                      )
        sty.configure("r.TButton",
                      foreground = "blue",
                      font = abtnf)
        sty.configure("f.TButton",
                      foreground = "magenta",
                      font = abtnf)
        sty.configure("q.TButton",
                      foreground = qbtnfg,
                      font = abtnf)
        sty.configure("sl.TButton",
                      foreground = "#ff0000",
                      font = abtnf)
        sty.configure("TEntry",
                      font = entf,
                      foreground = entfg,
                      background = entbg,
                      sticky = "ew",
                      width = 40,
                      )
        sty.configure("TCheckbutton",
                      foreground = ckbfg,
                      font = ckbf,
                      )
        sty.configure("TOptionMenu",
                      font = opnf,
                      foreground = entfg,
                      background = entbg,
                      )

        base.Globs["predatacallback"] = master.update
        base.Globs["version"] = "%.2f" % (float(version) + float(pgmversion))
        self.root.title("sta/lta event detection"
                        + "           version " + base.Globs["version"]
                        + "           "
                        + "   [gui " + version
                        + "   algorithm " + pgmversion + "]"
                        + "           "
                        + "theme: " + theme)
        self.truedatafile = ""
        self.statefile = ""
        self.isrunning = False


        row = 0
        row += 1
        lb = ttk.Label(master, text = "processing parameters",
                       style = "head.TLabel")
        lb.grid(row = row, column = 3, columnspan = 2)
        ttk.Label(master, text = " ").grid(row = row, column = 6, padx = 50)


        row += 1
        lb = ttk.Label(master, text = "Tsta ", style = "var.TLabel")
        lb.grid(row = row, column = 3, sticky = E)
        self.Tsta = StringVar(master, "0.25")
        ttk.Entry(master, textvariable = self.Tsta
                  ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " short time average window"
                  ).grid(row = row, column = 5, sticky = W)
        ttk.Label(master, text = "secs", style = "unit.TLabel"
                  ).grid(row = row, column = 6, sticky = W)

        row += 1
        ttk.Label(master, text = "Tlta ", style = "var.TLabel"
                  ).grid(row = row, column = 3, sticky = E)
        self.Tlta = StringVar()
        self.Tlta.set("90.0")
        ttk.Entry(master, textvariable = self.Tlta
                  ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " long time average window",
                  ).grid(row = row, column = 5, sticky = W)
        ttk.Label(master, text = "secs", style = "unit.TLabel"
                  ).grid(row = row, column = 6, sticky = W)

        row += 1
        ttk.Label(master, text = "Trigger ", style = "var.TLabel"
                  ).grid(row = row, column = 3, sticky = E)
        self.Triggerthreshold = StringVar()
        self.Triggerthreshold.set("5.0")
        ttk.Entry(master, textvariable = self.Triggerthreshold
                  ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " sta/lta trigger level"
                  ).grid(row = row, column = 5, sticky = W)
        ttk.Label(master, text = "ratio", style = "unit.TLabel",
                  ).grid(row = row, column = 6, sticky = W)

        row += 1
        ttk.Label(master, text = "Detrigger ", style = "var.TLabel",
                  ).grid(row = row, column = 3, sticky = E)
        self.Detriggerthreshold = StringVar()
        self.Detriggerthreshold.set("2.0")
        ttk.Entry(master, textvariable = self.Detriggerthreshold
                  ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " sta/lta de-trigger level"
                  ).grid(row = row, column = 5, sticky = W)
        ttk.Label(master, text = "ratio", style = "unit.TLabel",
                  ).grid(row = row, column = 6, sticky = W)

        row += 1
        ttk.Label(master, text = "Trigduration ", style = "var.TLabel",
                  ).grid(row = row, column = 3, sticky = E)
        self.Trigduration = StringVar()
        self.Trigduration.set("30.0")
        ttk.Entry(master, textvariable = self.Trigduration,
                  ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " post-trigger event duration"
                  ).grid(row = row, column = 5, sticky = W)
        ttk.Label(master, text = "secs", style = "unit.TLabel",
                  ).grid(row = row, column = 6, sticky = W)

        row += 1
        ttk.Label(master, text = "Trigdesense ", style = "var.TLabel",
                  ).grid(row = row, column = 3, sticky = E)
        self.Trigdsensetime = StringVar()
        self.Trigdsensetime.set("0.0")
        ttk.Entry(master, textvariable = self.Trigdsensetime,
                  ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " lta desense time scale"
                  ).grid(row = row, column = 5, sticky = W)
        ttk.Label(master, text = "secs", style = "unit.TLabel",
                  ).grid(row = row, column = 6, sticky = W)

        row += 1
        ttk.Label(master, text = "  ").grid(row = row, column = 3, sticky = W)

        row += 1
        ttk.Label(master, text = "logging parameters", style = "head.TLabel",
                  ).grid(row = row, column = 3, columnspan = 2)

        row += 1
        ttk.Label(master, text = "Loglevel ", style = "var.TLabel",
                  ).grid(row = row, column = 3, sticky = E)
        self.Loglevelsel = StringVar()
        self.Loglevelsel.set("debug")
        self.llb = ttk.OptionMenu(master, self.Loglevelsel,
                                  "debug", "debug", "info", "warning", "error")
        self.llb.grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " logging level"
                  ).grid(row = row, column = 5, sticky = W)


        row += 1
        ttk.Label(master, text = "Logfile ", style = "var.TLabel",
                  ).grid(row = row, column = 3, sticky = E)
        self.Logfile = StringVar()
        self.Logfile.set("")
        ttk.Entry(master, textvariable = self.Logfile
                  ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " log (txt) filename"
                  ).grid(row = row, column = 5, sticky = W)

        row += 1
        self.Outfile = StringVar()
        self.Outfile.set("")
        self.Outshowfile = StringVar()
        self.Outshowfile.set("")
        ttk.Button(master, text = "specify output file",
                   command = self.OnOutBrowse,
                   ).grid(row = row, column = 3, sticky = E, padx = 4)
        ttk.Entry(master, textvariable = self.Outshowfile
                  ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " data (sac) filename"
                  ).grid(row = row, column = 5, sticky = W)

        row += 1
        ttk.Label(master, text = "Eventfile ", style = "var.TLabel",
               ).grid(row = row, column = 3, sticky = E)
        self.Eventfile = StringVar()
        self.Eventfile.set("")
        ttk.Entry(master, textvariable = self.Eventfile
              ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " event (xlsx) filename"
              ).grid(row = row, column = 5, sticky = W)

        row += 1
        ttk.Label(master, text = "  ").grid(row = row, column = 3, sticky = W)

        row += 1
        ttk.Label(master, text = "control parameters", style = "head.TLabel",
              ).grid(row = row, column = 3, columnspan = 2)

        row += 1
        ttk.Label(master, text = "Jobduration ", style = "var.TLabel",
              ).grid(row = row, column = 3, sticky = E)
        self.Jobduration = StringVar()
        self.Jobduration.set("")
        ttk.Entry(master, textvariable = self.Jobduration
              ).grid(row = row, column = 4, sticky = E + W)
        ttk.Label(master, text = " acquisition duration"
              ).grid(row = row, column = 5, sticky = W)
        ttk.Label(master, text = "secs", style = "unit.TLabel",
                  ).grid(row = row, column = 6, sticky = W)

        row += 1
        self.Doalarm = IntVar()
        ckb = ttk.Checkbutton(master, text = "event alarm ",
                              variable = self.Doalarm)
        ckb.grid(row = row, column = 3, sticky = E)
        self.Alarmduration = StringVar()
        self.Alarmduration.set("2.0")
        ent = ttk.Entry(master, textvariable = self.Alarmduration)
        ent.grid(row = row, column = 4, sticky = E + W)
        lbl = ttk.Label(master, text = " alarm duration")
        lbl.grid(row = row, column = 5, sticky = W)
        lbl = ttk.Label(master, text = "secs", style = "unit.TLabel")
        lbl.grid(row = row, column = 6, sticky = W)

        row += 1
        lbl = ttk.Label(master, text = "  ")
        lbl.grid(row = row, column = 3, sticky = W)

        row += 1
        lbl = ttk.Label(master, text = "data source", style = "head.TLabel")
        lbl.grid(row = row, column = 3, columnspan = 2)


        row += 1
        self.Comcheck = IntVar()
        ckb = ttk.Checkbutton(master, text = "use comport",
                              variable = self.Comcheck)
        ckb.grid(row = row, column = 3, sticky = E)
        comportlist = []
        for name, desc, hwid in serialports():
            comportlist.append(name)
        if len(comportlist) == 0:
            comportlist = ["-none-", ]
        self.comport = StringVar()
        self.comport.set(comportlist[0])
        self.ports = ttk.OptionMenu(master, self.comport, comportlist[-1],
                                    *comportlist)
        self.ports.grid(row = row, column = 4, sticky = E + W)
        lbl = ttk.Label(master, text = " active comport")
        lbl.grid(row = row, column = 5, sticky = W)

        row += 1
        self.datafile = StringVar()
        self.datafile.set("")
        self.truedatafile = StringVar()
        self.truedatafile.set("")
        btn = ttk.Button(master, text = "select input file",
                         command = self.OnBrowse)
        btn.grid(row = row, column = 3, sticky = E, padx = 4)
        lbl = ttk.Label(master, text = " input (sac) file")
        lbl.grid(row = row, column = 5, sticky = W)
        ent = ttk.Entry(master, textvariable = self.datafile)
        ent.grid(row = row, column = 4, sticky = E + W)


        row += 1
        lbl = ttk.Label(master, text = "  ")
        lbl.grid(row = row, column = 3, sticky = W)

        row += 1
        lbl = ttk.Label(master, text = "display control",
                        style = "head.TLabel")
        lbl.grid(row = row, column = 3, columnspan = 2, sticky = E + W)


        row += 1
        self.doplot = IntVar()
        ckb = ttk.Checkbutton(master, text = "plot results",
                              variable = self.doplot)
        ckb.grid(row = row, column = 3, columnspan = 2, sticky = W)

        row += 1
        self.doplotavg = IntVar()
        ckb = ttk.Checkbutton(master, text = "show running averages",
                              variable = self.doplotavg)
        ckb.grid(row = row, column = 3, columnspan = 2, sticky = W,
                 padx = 20)

        row += 1
        self.doploty = IntVar()
        ckb = ttk.Checkbutton(master, text = "show trace",
                              variable = self.doploty)
        ckb.grid(row = row, column = 3, columnspan = 2, sticky = W,
                 padx = 20)

        row += 1
        self.doploth = IntVar()
        ckb = ttk.Checkbutton(master, text = "plot histograms",
                              variable = self.doploth)
        ckb.grid(row = row, column = 3, columnspan = 2, sticky = W,
                 padx = 20)

        row += 1
        self.showcommand = IntVar()
        ckb = ttk.Checkbutton(master, text = "show command line (debug)",
                              variable = self.showcommand)
        ckb.grid(row = row, column = 3, columnspan = 2, sticky = W)

        row += 1
        ttk.Label(master, text = "  ").grid(row = row, column = 3, sticky = W)

        row += 1
        col = 3
        self.runb = ttk.Button(master, text = "run", style = "r.TButton",
                               command = self.OnRun)
        self.runb.grid(row = row, column = col, sticky = N)
        col += 1
        self.finishb = ttk.Button(master, text = "finish",
                              style = "f.TButton",
                              command = self.OnFinish)
        self.finishb.grid(row = row, column = col, sticky = N)
        self.finishb.state(("disabled",))
        col += 1
        savb = ttk.Button(master, text = "save", command = self.saveState,
                          style = "sl.TButton")
        savb.grid(row = row, column = col, sticky = N)
        savb.state(("disabled",))
        col += 1
        loadb = ttk.Button(master, text = "load", command = self.loadState,
                           style = "sl.TButton")
        loadb.grid(row = row, column = col, sticky = W)
        loadb.state(("disabled",))
        col += 1
        btn = ttk.Button(master, text = "quit", style = "q.TButton",
                         command = self.OnQuit)
        btn.grid(row = row, column = col, sticky = N)
        col += 1
        lbl = ttk.Label(master, text = "      ")
        lbl.grid(row = row, column = col, sticky = W)


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
        self.runb.state(("disabled",))
        self.finishb.state(("!disabled",))
        self.isrunning = True
        r = pgmmain(args)
        self.isrunning = False
        self.finishb.state(("disabled",))
        self.runb.state(("!disabled",))
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
        self.frame.quit()


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

    options = "ht:l"

    theme = "alt"
    list_all = False

    try:
        try:
            opts, datafiles = getopt.getopt(argv[1:], options, ["help"])
        except getopt.error, msg:
            raise Usage(msg)

        # process options
        for o, a in opts:
            if o in ("-h", "--help"):
                print __doc__ + "\nversion: " + version
                sys.exit(0)
            elif o == "-l":
                list_all = True
            elif o == "-t":
                theme = a
            else:
                print "unknown argument: " + a
                print __doc__ + "\nversion: " + version
                sys.exit(1)

        if list_all:
            style = ttk.Style()
            print "available themes:"
            for t in style.theme_names():
                print "    " + t
            return 0

        app = App(theme)
        app.root.mainloop()
        try:
            app.root.destroy()
        except:
            pass

    except Exception, e:
        log().exception("gui error")
        print >> sys.stderr, e
        return 3


if __name__ == "__main__":
    sys.exit(main())
