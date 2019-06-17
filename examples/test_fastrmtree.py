
import os
import sys
import time
import shutil

import fastrmtree


def CreateDirs(baseDirName, dirCnt, fileCnt, level):
    if level > 0:
        for dn in range(dirCnt):
            dirName = os.path.join(baseDirName, "dir%d" % dn)
            CreateDirs(dirName, dirCnt, fileCnt, level - 1)
    else:
        os.makedirs(baseDirName)
        for fn in range(fileCnt):
            with open(os.path.join(baseDirName, "file%d" % fn), "wb") as O:
                O.write(b"12345678" * 100 * fn)


def CreateFakeTree(rootDirName):
    print("Create fake file tree...")
    for bdn in range(8):
        CreateDirs(os.path.join(rootDirName, "basedir%d" % bdn), 3, 16, 3)


if __name__ == "__main__":
    # First create a file tree for testing fastcopy and fastrmtree
    rootDirName = "TestFileTree"
    if os.path.exists(rootDirName):
        shutil.rmtree(rootDirName)
    CreateFakeTree(rootDirName)
    if os.name != "nt":
        os.sync()
    print("Remove test file tree with fastrmtree...")
    t1 = time.time()
    fastrmtree.main(rootDirName)
    print("Test file tree removed after %.1f seconds" % (time.time() - t1))
    if os.name != "nt":
        os.sync()
    CreateFakeTree(rootDirName)
    if os.name != "nt":
        os.sync()
    t1 = time.time()
    if os.name == "nt":
        print("Remove test file tree with shutil.rmtree...")
        shutil.rmtree(rootDirName)
    else:
        print("Remove test file tree with rm -rf...")
        os.system("rm -rf %s" % rootDirName)
    print("Test file tree removed after %.1f seconds" % (time.time() - t1))
