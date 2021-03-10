
import time
import gc
from collections import deque
from multiprocessing.pool import ThreadPool
import fastthreadpool
import zstandard as zstd
import msgpack


result = deque()


def worker(data):
    Z = zstd.ZstdDecompressor()
    return msgpack.unpackb(Z.decompress(data), use_list=False)


def worker_gc(data):
    gc.disable()
    Z = zstd.ZstdDecompressor()
    result = msgpack.unpackb(Z.decompress(data), use_list=False)
    gc.enable()
    return result


def result_cb(data):
    result.append(data)


def map_result_cb(data):
    result.extend(data)


packedData = zstd.ZstdCompressor(write_content_size=True, write_checksum=True, level=14).compress(msgpack.packb(list(range(5000)),
                                                                                                                use_bin_type=True))
packedValues = [packedData for _ in range(1000)]

t = time.time()
for value in packedValues:
    result.append(worker(value))
print("Single thread: %.3f" % (time.time() - t), len(result))
result.clear()

gc.disable()
t = time.time()
for value in packedValues:
    result.append(worker(value))
print("Single thread(no gc2): %.3f" % (time.time() - t), len(result))
result.clear()
gc.enable()

t = time.time()
pool = fastthreadpool.Pool()
pool.map(worker, packedValues)
pool.shutdown()
result = pool.done
print("fastthreadpool.map: %.3f" % (time.time() - t), len(result))
result.clear()

t = time.time()
pool = fastthreadpool.Pool()
pool.map(worker_gc, packedValues)
pool.shutdown()
result = pool.done
print("fastthreadpool.map(no gc): %.3f" % (time.time() - t), len(result))
result.clear()

gc.disable()
t = time.time()
pool = fastthreadpool.Pool()
pool.map(worker, packedValues)
pool.shutdown()
result = pool.done
print("fastthreadpool.map(no gc2): %.3f" % (time.time() - t), len(result))
result.clear()
gc.enable()

t = time.time()
pool = fastthreadpool.Pool()
for value in packedValues:
    pool.submit(worker, value)
pool.shutdown()
result = pool.done
print("fastthreadpool.submit: %.3f" % (time.time() - t), len(result))
result.clear()

gc.disable()
t = time.time()
pool = fastthreadpool.Pool()
for value in packedValues:
    pool.submit(worker, value)
pool.shutdown()
result = pool.done
print("fastthreadpool.submit(no gc2): %.3f" % (time.time() - t), len(result))
result.clear()
gc.enable()

t = time.time()
pool = ThreadPool()
pool.map_async(worker, packedValues, callback=map_result_cb)
pool.close()
pool.join()
print("multiprocessing.pool.ThreadPool.map_async: %.3f" % (time.time() - t), len(result))
result.clear()

gc.disable()
t = time.time()
pool = ThreadPool()
pool.map_async(worker, packedValues, callback=map_result_cb)
pool.close()
pool.join()
print("multiprocessing.pool.ThreadPool.map_async(no gc2): %.3f" % (time.time() - t), len(result))
result.clear()
gc.enable()

t = time.time()
pool = ThreadPool()
for value in packedValues:
    pool.apply_async(worker, (value, ), callback=result_cb)
pool.close()
pool.join()
print("multiprocessing.pool.ThreadPool.apply_async: %.3f" % (time.time() - t), len(result))
result.clear()

gc.disable()
t = time.time()
pool = ThreadPool()
for value in packedValues:
    pool.apply_async(worker, (value, ), callback=result_cb)
pool.close()
pool.join()
print("multiprocessing.pool.ThreadPool.apply_async(no gc2): %.3f" % (time.time() - t), len(result))
result.clear()
gc.enable()
