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


def Scanner(rootDirName):
    items = deque()
    for srcBaseDirName, dirNames, fileNames in scandir.walk(rootDirName):
        for dirName in dirNames:
            items.append((0, os.path.join(srcBaseDirName, dirName)))
        for fileName in fileNames:
            items.append((1, os.path.join(srcBaseDirName, fileName)))
    return items


def Remove(pathName):
    try:
        os.remove(pathName)
    except:
        os.chmod(pathName, stat.S_IWRITE)
        os.remove(pathName)


def main(rootDirName):
    fileTree = Scanner(rootDirName)
    dirTree = deque()
    with fastthreadpool.Pool(32) as pool:
        while fileTree:
            itemType, pathName = fileTree.pop()
            if itemType == 0:
                dirTree.append(pathName)
            else:
                pool.submit(Remove, pathName)
    while dirTree:
        dirName = dirTree.popleft()
        try:
            os.rmdir(dirName)
        except:
            dirTree.append(dirName)
    os.rmdir(rootDirName)


if __name__ == "__main__":
    t1 = time.time()
    main(sys.argv[1])
    print("Finished after %.1f seconds." % (time.time() - t1))
