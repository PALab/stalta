'''scan a log stream and extract event info'''

import re
import xlsxwriter as xls


def scanstream(stream, filename, Tsta, Tlta, Triggerthreshold,
               Detriggerthreshold, Trigdsensetime, sps):

    trigger_re = "^INFO (\S+) (\S+):\s+trigger\[(\d+)\] at (\S+)$"
    trigcre = re.compile(trigger_re)
    duration_re = "^INFO (\S+) (\S+):\s+event (\S+) sec\s+retrig\s+" \
                  + "(\S+)\s+rmax\s+(\S+)$"
    durcre = re.compile(duration_re)

    events = []
    state = "4event"
    try:
        while True:
            s = stream.get(False)
            if s is None:
                break
            s = s.strip()
            if len(s) == 0:
                continue
            if state == "4event":
                trig = re.match(trigcre, s)
                if trig is None:
                    continue
                rd, rt, trign, goodt = trig.groups()
                state = "4duration"
                # print goodt
            else:  # state == "4duration"
                dur = re.match(durcre, s)
                if dur is None:
                    continue
                xd, xt, tdur, nretrig, rmax = dur.groups()
                events.append((rd, rt, trign, goodt, tdur, nretrig, rmax))
                state = "4event"
                # print (rd, rt, trign, goodt, tdur)

    except:
        pass

    wb = xls.Workbook(filename)
    ws = wb.add_worksheet('events')

    bold_centered = wb.add_format({'bold': True, 'align': 'center'})
    bold_left = wb.add_format({'bold': True, 'align': 'left'})
    c = 0
    for name, value in (('sps', sps),
                        ('Tsta', Tsta),
                        ('Tlta', Tlta),
                        ('Tthr', Triggerthreshold),
                        ('Dthr', Detriggerthreshold),
                        ('Fdes', Trigdsensetime)):
        ws.write(0, c, "%s: %.2f" % (name, value), bold_left)
        c += 1
    ws.write('A2', 'date', bold_centered)
    ws.write('B2', 'time', bold_centered)
    ws.write('C2', 'event id', bold_centered)
    ws.write('D2', 'event time', bold_centered)
    ws.write('E2', 'duration', bold_centered)
    ws.write('F2', 'retriggers', bold_centered)
    ws.write('G2', 'max(ratio)', bold_centered)

    ws.set_column("A:G", 14, wb.add_format({'align': 'center'}))

    r = 2
    for evlist in events:
        c = 0
        for e in evlist:
            ws.write(r, c, e)
            c += 1
        r += 1

    wb.close()
