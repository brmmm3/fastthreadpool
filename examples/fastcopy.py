# Copyright 2019 Martin Bammer. All Rights Reserved.
# Licensed under MIT license.

# Parallelized version of copytree. Much faster on Windows.
# Linux is fast by default without multithreading workaround.

import os
import sys
import time
import traceback
from collections import deque
from threading import Event

import fastthreadpool


def Scanner(rootDirName, items, evt):
    rootDirNameLen = len(rootDirName) + 1
    path_join = os.path.join
    try:
        for srcBaseDirName, dirNames, fileNames in os.walk(rootDirName):
            for dirName in dirNames:
                items.append((0, path_join(srcBaseDirName[rootDirNameLen:], dirName)))
            for fileName in fileNames:
                items.append((1, path_join(srcBaseDirName[rootDirNameLen:], fileName)))
            if items:
                evt.set()
    except:
        items.append((-1, traceback.format_exc()))
    items.append((2, None))


def Copy(srcPathName, dstPathName):
    BS = 65536
    MINBS = 65536
    MAXBS = 1024 * 1024
    time_time = time.time
    try:
        with open(dstPathName, "wb") as W:
            with open(srcPathName, "rb") as R:
                while True:
                    t1 = time_time()
                    data = R.read(BS)
                    if not data:
                        break
                    dt = time_time() - t1
                    W.write(data)
                    if (BS < MAXBS) and (dt < 0.1):
                        BS <<= 1
                    elif (BS > MINBS) and (dt > 0.5):
                        BS >>= 1
            W.flush()
    except:
        traceback.print_exc()


def main(rootDirName, dstBaseDirName):
    if not os.path.exists(dstBaseDirName):
        os.makedirs(dstBaseDirName)
    itemsScanner = deque()
    evtScanner = Event()
    bFinishing = False
    path_join = os.path.join
    with fastthreadpool.Pool(32) as pool:
        pool.submit(Scanner, rootDirName, itemsScanner, evtScanner)
        while not bFinishing or itemsScanner or (pool.pending > 0):
            try:
                itemType, relPathName = itemsScanner.popleft()
            except IndexError:
                evtScanner.wait(0.1)
                evtScanner.clear()
                continue
            if itemType == 0:
                dirName = path_join(dstBaseDirName, relPathName)
                if not os.path.exists(dirName):
                    os.makedirs(dirName)
            elif itemType == 1:
                pool.submit(Copy, path_join(rootDirName, relPathName), path_join(dstBaseDirName, relPathName))
            elif itemType == 2:
                bFinishing = True
            else:
                print("ERROR:", relPathName)
                break
            while pool.failed:
                print(pool.failed.popleft())


if __name__ == "__main__":
    t1 = time.time()
    main(sys.argv[1], sys.argv[2])
    print("Finished after %.1f seconds." % (time.time() - t1))
