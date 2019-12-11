# Copied with minimal modifications from curio
# https://github.com/dabeaz/curio


import time
import argparse
from socket import socket, AF_UNIX, AF_INET, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY, SHUT_WR

from concurrent.futures import ProcessPoolExecutor


def run_test(bUnix, addr, msg, REQSIZE, n, mpr, bDisconnect):
    if mpr:
        n //= mpr
    if bUnix:
        sock = socket(AF_UNIX, SOCK_STREAM)
    else:
        sock = socket(AF_INET, SOCK_STREAM)
    try:
        sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
    except (OSError, NameError):
        pass
    sock.connect(addr)
    while n > 0:
        sock.sendall(msg)
        if bDisconnect:
            sock.shutdown(SHUT_WR)
        nrecv = 0
        while nrecv < REQSIZE:
            resp = sock.recv(REQSIZE)
            if not resp:
                raise SystemExit()
            nrecv += len(resp)
        n -= 1
        if bDisconnect:
            sock.close()
            if bUnix:
                sock = socket(AF_UNIX, SOCK_STREAM)
            else:
                sock = socket(AF_INET, SOCK_STREAM)
            try:
                sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
            except (OSError, NameError):
                pass
            sock.connect(addr)


def main(args):
    bUnix = False
    if args.addr.startswith('file:'):
        bUnix = True
        addr = args.addr[5:]
    else:
        addr = args.addr.split(':')
        addr[1] = int(addr[1])
        addr = tuple(addr)
    print('will connect to: {}'.format(addr))

    MSGSIZE = args.msize
    REQSIZE = MSGSIZE * args.mpr

    msg = b'x'*(MSGSIZE - 1) + b'\n'
    if args.mpr:
        msg *= args.mpr
    TIMES = args.times
    N = args.workers
    NMESSAGES = args.num
    print(f'Sending {NMESSAGES} messages in {N} processes...')
    start = time.time()
    for _ in range(TIMES):
        with ProcessPoolExecutor(max_workers=N) as e:
            for _ in range(N):
                e.submit(run_test, bUnix, addr, msg, REQSIZE, NMESSAGES, args.mpr, args.disconnect)
    end = time.time()
    duration = end - start
    msgCnt = NMESSAGES * N * TIMES
    msgSpeed = msgCnt / duration
    mbSpeed = msgSpeed * MSGSIZE / 1024 / 1024
    print(f'{msgCnt} messages with {MSGSIZE} bytes size in {duration:.2f} seconds')
    print(f'{int(msgSpeed)} messages/s')
    print(f'{mbSpeed:.2f} MB/s')
    return msgSpeed, mbSpeed


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--msize', default=1000, type=int,
                        help='message size in bytes')
    parser.add_argument('--mpr', default=1, type=int,
                        help='messages per request')
    parser.add_argument('--num', default=200000, type=int,
                        help='number of messages')
    parser.add_argument('--times', default=1, type=int,
                        help='number of times to run the test')
    parser.add_argument('--workers', default=3, type=int,
                        help='number of workers')
    parser.add_argument('--addr', default='127.0.0.1:25000', type=str,
                        help='address:port of echoserver')
    parser.add_argument('--disconnect', default=False, action='store_true',
                        help='disconnect after every message')
    main(parser.parse_args())
