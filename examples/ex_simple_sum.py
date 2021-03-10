
import time
from multiprocessing.pool import ThreadPool
import fastthreadpool


def worker(value):
    return value


class Result:
    result = 0


def result_cb(value):
    Result.result += value


def map_result_cb(values):
    Result.result += sum(values)


data = list(range(50000))

result = 0
t = time.time()
for value in data:
    result += value
print("%.3f" % (time.time() - t), result)

t = time.time()
for value in data:
    Result.result += value
print("%.3f" % (time.time() - t), Result.result)
Result.result = 0

t = time.time()
pool = fastthreadpool.Pool()
pool.map(worker, data)
pool.shutdown()
result = sum(pool.done)
print("%.3f" % (time.time() - t), result)

t = time.time()
pool = fastthreadpool.Pool()
for value in data:
    pool.submit(worker, value)
pool.shutdown()
result = sum(pool.done)
print("%.3f" % (time.time() - t), result)

t = time.time()
pool = ThreadPool()
pool.map_async(worker, data, callback=map_result_cb)
pool.close()
pool.join()
print("%.3f" % (time.time() - t), Result.result)

t = time.time()
pool = ThreadPool()
for value in data:
    pool.apply_async(worker, (value, ), callback=result_cb)
pool.close()
pool.join()
print("%.3f" % (time.time() - t), Result.result)
