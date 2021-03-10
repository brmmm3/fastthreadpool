
import os
import time

import fastcopy


def CreateDirs(baseDirName, dirCnt, fileCnt, level):
    if level > 0:
        for dn in range(dirCnt):
            dirName = os.path.join(baseDirName, "dir%d" % dn)
            CreateDirs(dirName, dirCnt, fileCnt, level - 1)
    else:
        os.makedirs(baseDirName)
        for fn in range(fileCnt):
            with open(os.path.join(baseDirName, "file%d" % fn), "wb") as F:
                F.write(b"12345678" * 100 * fn)


def CreateFakeTree(rootDirName):
    print("Create fake file tree...")
    for bdn in range(10):
        CreateDirs(os.path.join(rootDirName, "basedir%d" % bdn), 4, 16, 4)


if __name__ == "__main__":
    # First create a file tree for testing fastcopy and fastrmtree
    rootDirName = "TestFileTree"
    CreateFakeTree(rootDirName)
    os.sync()
    print("Copy test file tree with fastcopy...")
    t1 = time.time()
    fastcopy.main(rootDirName, rootDirName + "Dst")
    print("Test file tree copied after %.1f seconds" % (time.time() - t1))
    os.sync()
    print("Remove test file tree with rm -rf...")
    t1 = time.time()
    os.system("rm -rf %sDst" % rootDirName)
    print("Test file tree removed after %.1f seconds" % (time.time() - t1))
    print("Copy test file tree with cp -r...")
    t1 = time.time()
    os.system("cp -r %s %sDst" % (rootDirName, rootDirName))
    print("Test file tree copied after %.1f seconds" % (time.time() - t1))
    os.system("rm -rf %s" % rootDirName)
    os.system("rm -rf %sDst" % rootDirName)
