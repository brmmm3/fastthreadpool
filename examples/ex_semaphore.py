
import time
import threading
import fastthreadpool
from multiprocessing.pool import ThreadPool

t = time.time()
s = threading.Semaphore()
for _ in range(200000):
    s.release()
    s.acquire()
print("threading.Semaphore", time.time() - t)

t = time.time()
s = fastthreadpool.Semaphore()
for _ in range(200000):
    s.release()
    s.acquire()
print("fastthreadpool.Semaphore", time.time() - t)


def Worker(i):
    s.release()
    s.acquire()

t = time.time()
pool = ThreadPool()
s.release()
s.release()
pool.map(Worker, range(200000))
pool.close()
pool.join()
print("ThreadPool.map", time.time() - t)

t = time.time()
pool = fastthreadpool.Pool()
s.release()
s.release()
pool.map(Worker, range(200000))
pool.shutdown()
print("fastthreadpool.map", time.time() - t)
