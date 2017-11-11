#!/usr/bin/env python2
from __future__ import print_function
import sys
import os
import socket
import struct
import argparse
import threading
import traceback
import OSC

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

    osc.server_activate()

    osc.addMsgHandler("default", handle_osc)

    osc.serve_forever()


def handle_osc(addr, tags, stuff, source):
    data_info = " ".join("{}:{}".format(typ, val) for typ, val in zip(tags, stuff))

    print("[{}:{}] {}  {}".format(source[0], source[1], addr, data_info))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', metavar='ADDR', help='multicast source address')
    parser.add_argument('port', metavar='PORT', type=int, help='multicast source port')
    parser.add_argument('-i', '--iface', default="0.0.0.0", metavar='IFADDR', help='interface address for multicast input')

    try:
        main(parser.parse_args())

    except KeyboardInterrupt:
        pass

    except SystemExit:
        raise

    except:
        traceback.print_exc()
        sys.exit(1)

    sys.exit(0)

