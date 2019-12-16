
import time
import gc
from multiprocessing.pool import ThreadPool
import fastthreadpool
import zstandard as zstd
import msgpack


def worker(data):
    return zstd.ZstdCompressor(write_content_size=True, write_checksum=True, level=14).compress(msgpack.packb(data, use_bin_type=True))


def worker_gc(data):
    gc.disable()
    result = zstd.ZstdCompressor(write_content_size=True, write_checksum=True, level=14).compress(msgpack.packb(data, use_bin_type=True))
    gc.enable()
    return result


def result_cb(data):
    result.append(data)


def map_result_cb(data):
    result.extend(data)


if __name__ == "__main__":
    data = [list(range(40000)) for _ in range(1000)]

    t = time.time()
    pool = fastthreadpool.Pool()
    result = pool.done
    pool.map(worker, data)
    pool.shutdown()
    print("fastthreadpool.map: %.3f" % (time.time() - t), len(result))
    result.clear()

    t = time.time()
    pool = fastthreadpool.Pool()
    result = pool.done
    pool.map(worker_gc, data)
    pool.shutdown()
    print("fastthreadpool.map(no gc): %.3f" % (time.time() - t), len(result))
    result.clear()

    gc.disable()
    t = time.time()
    pool = fastthreadpool.Pool()
    result = pool.done
    pool.map(worker, data)
    pool.shutdown()
    print("fastthreadpool.map(no gc2): %.3f" % (time.time() - t), len(result))
    result.clear()
    gc.enable()

    t = time.time()
    pool = fastthreadpool.Pool()
    result = pool.done
    for value in data:
        pool.submit(worker, value)
    pool.shutdown()
    print("fastthreadpool.submit: %.3f" % (time.time() - t), len(result))
    result.clear()

    t = time.time()
    pool = ThreadPool()
    pool.map_async(worker, data, callback=map_result_cb)
    pool.close()
    pool.join()
    print("multiprocessing.pool.ThreadPool.map_async: %.3f" % (time.time() - t), len(result))
    result.clear()

    t = time.time()
    pool = ThreadPool()
    for value in data:
        pool.apply_async(worker, (value, ), callback=result_cb)
    pool.close()
    pool.join()
    print("multiprocessing.pool.ThreadPool.apply_async: %.3f" % (time.time() - t), len(result))
    result.clear()

    t = time.time()
    for value in data:
        result.append(worker(value))
    print("Single thread: %.3f" % (time.time() - t), len(result))
    result.clear()
