#!/usr/bin/env python2
"""
Current issue: OSCServer: error on request from 10.0.0.110:44348: can't start new thread
"""
from __future__ import print_function
import sys
import os
import socket
import struct
import argparse
import threading
import traceback
import OSC
import curses
import time

scr = None

COLOR_GOOD = 2
COLOR_WARN = 8
COLOR_ERROR = 9

header = "Source".ljust(28) + \
         "Path".ljust(40) + \
         "Data"

osc_entries = {}
out_lock = None


class OscEntry(object):
    path = ''
    source = ('', 0)
    data = []
    last = 0.0

    def update(self, source, path, data):
        self.source = source
        self.path = path
        self.data = data
        self.last = time.time()


def handle_osc(addr, tags, stuff, source):
    entry = osc_entries.setdefault(addr, OscEntry())
    entry.update(source, addr, stuff)
    display_update()


def display_update():
    now = time.time()

    for index, key in enumerate(sorted(osc_entries.keys())):
        color = COLOR_GOOD
        entry = osc_entries[key]

        if now - entry.last >= 20.0:
            del osc_entries[key]
        elif now - entry.last >= 10.0:
            color = COLOR_ERROR
        elif now - entry.last >= 5.0:
            color = COLOR_WARN

        source = "[{}:{}]".format(*entry.source)

        data_summary = ''

        for data_item in entry.data:
            if isinstance(data_item, float):
                data_item = "{:.03}".format(round(data_item, 3))

            data_summary += str(data_item).ljust(12)

        summary = "{:<26}  {:<38} {:<60}".format(
            source, entry.path, data_summary
        )

        if not params.no_curses:
            try:
                scr.addstr(index + 2, 0, summary, curses.color_pair(color))
            except:
                pass
        else:
            out_lock.acquire()
            print(summary)
            out_lock.release()

    if not params.no_curses:
        for index in range(len(osc_entries), len(osc_entries)+10):
            try:
                scr.addstr(index + 2, 0, " " * 140)
            except:
                pass

        scr.addstr(0, 0, header)
        # scr.addstr(36, 0, '')
        scr.refresh()


def main(args):
    addr = (args.addr, args.port)
    osc = OSC.ThreadingOSCServer(addr, bind_and_activate=False)

    # setup multicast
    osc.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    osc.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    osc.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    osc.server_bind()
    mcast_iface_aton = socket.inet_aton(args.iface)
    osc.socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, mcast_iface_aton)
    mreq = socket.inet_aton(args.addr) + mcast_iface_aton
    osc.socket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    osc.timeout = 0.1

    if not args.no_curses:
        osc.handle_timeout = display_update
    else:
        global out_lock
        out_lock = threading.Lock()

    osc.server_activate()

    osc.addMsgHandler("default", handle_osc)

    osc.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', metavar='ADDR', help='multicast source address')
    parser.add_argument('port', metavar='PORT', type=int, help='multicast source port')
    parser.add_argument('-i', '--iface', default="0.0.0.0", metavar='IFADDR', help='interface address for multicast input')
    parser.add_argument('-n', '--no-curses', action='store_true', help='do not use curses')

    params = None

    try:
        params = parser.parse_args()

        if not params.no_curses:
            scr = curses.initscr()

            curses.noecho()
            curses.cbreak()
            curses.start_color()
            curses.use_default_colors()

            if curses.can_change_color():
                curses.init_color(curses.COLOR_BLACK, 0, 0, 0)
                curses.init_color(curses.COLOR_WHITE, 255, 255, 255)
                curses.init_color(curses.COLOR_GREEN, 0, 255, 0)
                curses.init_color(curses.COLOR_YELLOW, 255, 255, 0)
                curses.init_color(curses.COLOR_RED, 255, 0, 0)
                curses.init_color(curses.COLOR_MAGENTA, 255, 0, 255)

            curses.init_pair(1, curses.COLOR_WHITE, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN)
            curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_RED)
            curses.init_pair(10, curses.COLOR_YELLOW, -1)

        main(params)

    except KeyboardInterrupt:
        pass

    except SystemExit:
        raise

    except:
        if params and not params.no_curses:
            curses.echo()
            curses.nocbreak()
            curses.endwin()

        traceback.print_exc()
        sys.exit(1)

    finally:
        if params and not params.no_curses:
            curses.echo()
            curses.nocbreak()
            curses.endwin()

    sys.exit(0)

