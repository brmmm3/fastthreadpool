
import time
import threading
import fastthreadpool

t = time.time()
s = fastthreadpool.Semaphore()
for _ in range(100000):
    s.release()
    s.acquire()
print(time.time() - t)

t = time.time()
s = threading.Semaphore()
for _ in range(100000):
    s.release()
    s.acquire()
print(time.time() - t)

