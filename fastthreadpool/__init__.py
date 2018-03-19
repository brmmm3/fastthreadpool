
import sys

if sys.version_info[0] > 2:
    from fastthreadpool.fastthreadpool import Pool, TimerObj, Semaphore, PoolCallback, PoolStopped, shutdown
else:
    from fastthreadpool import Pool, TimerObj, Semaphore, PoolCallback, PoolStopped, shutdown

