
import os
import sys
import time
import scandir
import traceback
from collections import deque
from threading import Event

import fastthreadpool


def Scanner(rootDirName, dstBaseDirName, items, evt):
    rootDirNameLen = len(rootDirName) + 1
    path_join = os.path.join
    try:
        for srcBaseDirName, dirNames, fileNames in scandir.walk(rootDirName):
            relDirName = srcBaseDirName[rootDirNameLen:]
            for dirName in dirNames:
                pathName = os.path.join(dstBaseDirName, relDirName, dirName)
                if not os.path.exists(pathName):
                    os.mkdir(pathName)
            for fileName in fileNames:
                items.append(path_join(relDirName, fileName))
            if items:
                evt.set()
    except:
        traceback.print_exc()
    items.append(None)


def Copy(srcPathName, dstPathName):
    try:
        #print("COPY", srcPathName, dstBaseDirName)
        BS = 65536
        MINBS = 65536
        MAXBS = 1024 * 1024
        time_time = time.time
        with open(dstPathName, "wb") as O:
            with open(srcPathName, "rb") as I:
                while True:
                    t1 = time_time()
                    data = I.read(BS)
                    if not data:
                        break
                    dt = time_time() - t1
                    O.write(data)
                    if (BS < MAXBS) and (dt < 0.1):
                        BS <<= 1
                    elif (BS > MINBS) and (dt > 0.5):
                        BS >>= 1
            O.flush()
    except:
        traceback.print_exc()


if __name__ == "__main__":
    rootDirName = sys.argv[1]
    dstBaseDirName = sys.argv[2]
    if not os.path.exists(dstBaseDirName):
        os.makedirs(dstBaseDirName)
    itemsScanner = deque()
    evtScanner = Event()
    bFinishing = False
    t1 = time.time()
    with fastthreadpool.Pool(32, done_callback=False) as pool:
        pool.submit(Scanner, rootDirName, dstBaseDirName, itemsScanner, evtScanner)
        while not bFinishing or itemsScanner or (pool.pending > 0):
            try:
                relPathName = itemsScanner.popleft()
            except IndexError:
                evtScanner.wait(0.1)
                evtScanner.clear()
                continue
            if relPathName is None:
                bFinishing = True
            else:
                pool.submit(Copy, os.path.join(rootDirName, relPathName), os.path.join(dstBaseDirName, relPathName))
            while pool.failed:
                print(pool.failed.popleft())
    print("Finished after %.1f seconds." % (time.time() - t1))
