# Copyright 2019 Martin Bammer. All Rights Reserved.
# Licensed under MIT license.

# Parallelized version of rmtree. Much faster on Windows.
# Linux is fast by default without multithreading workaround.

import os
import sys
import time
import stat
import scandir
from collections import deque

import fastthreadpool


def SafeRemove(exc, args, kwargs):
    try:
        os.chmod(args[0], stat.S_IWRITE)
        os.remove(args[0])
    except Exception as exc:
        print(exc)


def Scanner(rootDirName, pool):
    dirs2Remove = deque()
    path_join = os.path.join
    for srcBaseDirName, dirNames, fileNames in scandir.walk(rootDirName):
        for dirName in dirNames:
            dirs2Remove.append(path_join(srcBaseDirName, dirName))
        for fileName in fileNames:
            pool.submit(os.remove, path_join(srcBaseDirName, fileName))
    return dirs2Remove


def main(rootDirName):
    with fastthreadpool.Pool(32, done_callback=False, failed_callback=SafeRemove) as pool:
        dirs2Remove = Scanner(rootDirName, pool)
        failedDirs = None
        for _ in range(5):
            failedDirs = deque()
            while dirs2Remove:
                dirName = dirs2Remove.pop()
                try:
                    os.rmdir(dirName)
                except:
                    failedDirs.append(dirName)
            if not failedDirs:
                break
            dirs2Remove = failedDirs
        if failedDirs:
            for dirName in failedDirs:
                print("ERROR: Failed to remove directory:", dirName)
    os.rmdir(rootDirName)


if __name__ == "__main__":
    t1 = time.time()
    main(sys.argv[1])
    print("Finished after %.1f seconds." % (time.time() - t1))
