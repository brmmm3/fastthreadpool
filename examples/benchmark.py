
import sys
import time
import threading
import fastthreadpool
from multiprocessing.pool import ThreadPool
import zstd
import msgpack
if sys.version_info[0] > 2:
    from concurrent.futures import ThreadPoolExecutor


class TestSemaphore(object):

    def __init__(self):
        pass

    def acquire_cb(self, s):
        s.acquire()

    def release_cb(self, s):
        s.release()

    def fastthreadpool_Semaphore(self, values):
        s = fastthreadpool.Semaphore()
        for _ in values:
            s.release()
            s.acquire()
        return 0

    def threading_Semaphore(self, values):
        s = threading.Semaphore(0)
        for _ in values:
            s.release()
            s.acquire()
        return s._value

    def fastthreadpool_Semaphore_threads(self, values):
        s = fastthreadpool.Semaphore()
        pool = fastthreadpool.Pool()
        for value in values:
            if value & 1:
                pool.submit(self.release_cb, s)
            else:
                pool.submit(self.acquire_cb, s)
        pool.shutdown()
        return s._value

    def threading_Semaphore_threads(self, values):
        s = threading.Semaphore(0)
        pool = fastthreadpool.Pool()
        for value in values:
            if value & 1:
                pool.submit(self.release_cb, s)
            else:
                pool.submit(self.acquire_cb, s)
        pool.shutdown()
        return s._value

    def test(self, test_cb, data):
        t = time.time()
        result = getattr(self, test_cb)(data)
        print("%7.3f %d %s" % (time.time() - t, result, test_cb))

    def run(self, cnt):
        values = list(range(cnt))
        self.test("fastthreadpool_Semaphore", values)
        self.test("threading_Semaphore", values)
        self.test("fastthreadpool_Semaphore_threads", values)
        self.test("threading_Semaphore_threads", values)


class TestValues(object):

    def __init__(self):
        self.result = 0
        self.worker = None
        self.worker_gen = None
        self.lock = threading.Lock()

    def worker_cb(self, data):
        return data

    def worker_gen_cb(self, data):
        yield data

    def failed_cb(self, exc):
        print(exc)

    def result_cb(self, result):
        self.result += result

    def locked_result_cb(self, result):
        with self.lock:
            self.result += result

    def results_cb(self, results):
        self.result += sum(results)

    def locked_result_future_cb(self, result):
        with self.lock:
            self.result += result.result()

    def map(self, data):
        pool = fastthreadpool.Pool()
        pool.map(self.worker, data)
        pool.shutdown()
        self.result = sum(pool.done)

    def map_no_done(self, data):
        pool = fastthreadpool.Pool()
        pool.map(self.worker, data, False)
        pool.shutdown()

    def map_done_cb(self, data):
        with fastthreadpool.Pool(done_callback = self.result_cb) as pool:
            pool.map(self.worker, data)

    def map_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        pool.map(self.worker, data)
        pool.shutdown()
        self.result = sum(pool.done)

    def imap(self, data):
        pool = fastthreadpool.Pool()
        pool.imap(self.worker_gen, data)
        pool.shutdown()
        self.result = sum(pool.done)

    def imap_done_cb(self, data):
        with fastthreadpool.Pool(done_callback = self.result_cb) as pool:
            pool.imap(self.worker_gen, data)

    def imap_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        pool.imap(self.worker_gen, data)
        pool.shutdown()
        self.result = sum(pool.done)

    def submit(self, data):
        pool = fastthreadpool.Pool()
        for value in data:
            pool.submit(self.worker, value)
        pool.shutdown()
        self.result = sum(pool.done)

    def submit_pool_done_cb(self, data):
        with fastthreadpool.Pool(done_callback = self.result_cb) as pool:
            for value in data:
                pool.submit(self.worker, value)

    def submit_pool_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        for value in data:
            pool.submit(self.worker, value)
        pool.shutdown()
        self.result = sum(pool.done)

    def submit_done_cb(self, data):
        # Important: The result function is executed in the worker thread. So we need a
        #   lock in the result function!
        with fastthreadpool.Pool() as pool:
            for value in data:
                pool.submit_done(self.worker, self.locked_result_cb, value)

    def ThreadPool_map(self, data):
        pool = ThreadPool()
        results = pool.map(self.worker, data)
        pool.close()
        pool.join()
        self.result = sum(results)

    def ThreadPool_map_async_done_cb(self, data):
        pool = ThreadPool()
        pool.map_async(self.worker, data, callback = self.results_cb)
        pool.close()
        pool.join()

    def ThreadPool_apply_async_done_cb(self, data):
        pool = ThreadPool()
        for value in data:
            pool.apply_async(self.worker, ( value, ), callback = self.result_cb)
        pool.close()
        pool.join()

    def ThreadPoolExecutor_map(self, data):
        pool = ThreadPoolExecutor()
        results = pool.map(self.worker, data)
        pool.shutdown()
        self.result = sum(results)

    def ThreadPoolExecutor_submit_done_cb(self, data):
        # Important: The result function is executed in the worker thread. So we need a
        #   lock in the result function!
        pool = ThreadPoolExecutor()
        for value in data:
            future = pool.submit(self.worker, value)
            future.add_done_callback(self.locked_result_future_cb)
        pool.shutdown()

    def test(self, test_cb, data):
        self.result = 0
        self.worker = self.worker_cb
        self.worker_gen = self.worker_gen_cb
        t = time.time()
        getattr(self, test_cb)(data)
        print("%7.3f %12d %s" % (time.time() - t, self.result, test_cb))

    def run(self, cnt):
        print("\n%d values:" % cnt)
        values = list(range(cnt))
        self.result = 0
        t = time.time()
        for value in values:
            self.result_cb(self.worker_cb(value))
        print("%7.3f %12d single threaded" % (time.time() - t, self.result))
        t = time.time()
        self.result = sum([ self.worker_cb(value) for value in values ])
        print("%7.3f %12d sum list" % (time.time() - t, self.result))
        print("fastthreadpool:")
        self.test("map", values)
        self.test("map_no_done", values)
        self.test("map_done_cb", values)
        self.test("map_failed_cb", values)
        self.test("imap", values)
        self.test("imap_done_cb", values)
        self.test("imap_failed_cb", values)
        self.test("submit", values)
        self.test("submit_pool_done_cb", values)
        self.test("submit_pool_failed_cb", values)
        self.test("submit_done_cb", values)
        print("multiprocessing.pool.ThreadPool:")
        self.test("ThreadPool_map", values)
        self.test("ThreadPool_map_async_done_cb", values)
        self.test("ThreadPool_apply_async_done_cb", values)
        print("concurrent.futures.ThreadPoolExecutor:")
        self.test("ThreadPoolExecutor_map", values)
        self.test("ThreadPoolExecutor_submit_done_cb", values)


class TestLists(object):

    def __init__(self):
        self.result = 0
        self.worker = None
        self.worker_gen = None
        self.lock = threading.Lock()

    def worker_cb(self, data):
        return data

    def worker_gen_cb(self, data):
        yield data

    def failed_cb(self, exc):
        print(exc)

    def result_cb(self, result):
        self.result += sum(result)

    def locked_result_cb(self, result):
        with self.lock:
            self.result += sum(result)

    def results_cb(self, results):
        self.result += sum([ sum(result) for result in results ])

    def locked_result_future_cb(self, result):
        with self.lock:
            self.result += sum(result.result())

    def map(self, data):
        pool = fastthreadpool.Pool()
        pool.map(self.worker, data)
        pool.shutdown()
        self.result = sum([ sum(result) for result in pool.done ])

    def map_done_cb(self, data):
        pool = fastthreadpool.Pool(done_callback = self.result_cb)
        pool.map(self.worker, data)
        pool.shutdown()

    def map_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        pool.map(self.worker, data)
        pool.shutdown()
        self.result = sum([ sum(result) for result in pool.done ])

    def imap(self, data):
        pool = fastthreadpool.Pool()
        pool.imap(self.worker_gen, data)
        pool.shutdown()
        self.result = sum([ sum(result) for result in pool.done ])

    def imap_done_cb(self, data):
        pool = fastthreadpool.Pool(done_callback = self.result_cb)
        pool.imap(self.worker_gen, data)
        pool.shutdown()

    def imap_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        pool.imap(self.worker_gen, data)
        pool.shutdown()
        self.result = sum([ sum(result) for result in pool.done ])

    def submit(self, data):
        pool = fastthreadpool.Pool()
        for value in data:
            pool.submit(self.worker, value)
        pool.shutdown()
        self.result = sum([ sum(result) for result in pool.done ])

    def submit_done_cb(self, data):
        pool = fastthreadpool.Pool(done_callback = self.result_cb)
        for value in data:
            pool.submit(self.worker, value)
        pool.shutdown()

    def submit_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        for value in data:
            pool.submit(self.worker, value)
        pool.shutdown()
        self.result = sum([ sum(result) for result in pool.done ])

    def ThreadPool_map(self, data):
        pool = ThreadPool()
        results = pool.map(self.worker, data)
        pool.close()
        pool.join()
        self.result = sum([ sum(result) for result in results ])

    def ThreadPool_map_async_done_cb(self, data):
        pool = ThreadPool()
        pool.map_async(self.worker, data, callback = self.results_cb)
        pool.close()
        pool.join()

    def ThreadPool_apply_async_done_cb(self, data):
        pool = ThreadPool()
        for value in data:
            pool.apply_async(self.worker, ( value, ), callback = self.result_cb)
        pool.close()
        pool.join()

    def ThreadPoolExecutor_map(self, data):
        pool = ThreadPoolExecutor()
        results = pool.map(self.worker, data)
        pool.shutdown()
        self.result = sum([ sum(result) for result in results ])

    def ThreadPoolExecutor_submit_done_cb(self, data):
        pool = ThreadPoolExecutor()
        for value in data:
            future = pool.submit(self.worker, value)
            future.add_done_callback(self.locked_result_future_cb)
        pool.shutdown()

    def test(self, test_cb, data):
        self.result = 0
        self.worker = self.worker_cb
        self.worker_gen = self.worker_gen_cb
        t = time.time()
        getattr(self, test_cb)(data)
        print("%6.3f %10d %s" % (time.time() - t, self.result, test_cb))

    def run(self, n, cnt):
        print("\n%d lists with %d values:" % (n, cnt))
        v = list(range(cnt))
        values = [ v for _ in range(n) ]
        self.result = 0
        t = time.time()
        for value in values:
            self.result_cb(self.worker_cb(value))
        print("%6.3f %10d single threaded" % (time.time() - t, self.result))
        print("fastthreadpool:")
        self.test("map", values)
        self.test("map_done_cb", values)
        self.test("map_failed_cb", values)
        self.test("imap", values)
        self.test("imap_done_cb", values)
        self.test("imap_failed_cb", values)
        self.test("submit", values)
        self.test("submit_done_cb", values)
        self.test("submit_failed_cb", values)
        print("multiprocessing.pool.ThreadPool:")
        self.test("ThreadPool_map", values)
        self.test("ThreadPool_map_async_done_cb", values)
        self.test("ThreadPool_apply_async_done_cb", values)
        print("concurrent.futures.ThreadPoolExecutor:")
        self.test("ThreadPoolExecutor_map", values)
        self.test("ThreadPoolExecutor_submit_done_cb", values)


class TestCompress(object):

    def __init__(self):
        self.result = []
        self.worker = None
        self.worker_gen = None
        self.lock = threading.Lock()

    def compress_cb(self, data):
        return zstd.ZstdCompressor(write_content_size = True, write_checksum = True,
                                   level = 14).compress(data)

    def compress_gen_cb(self, data):
        yield zstd.ZstdCompressor(write_content_size = True, write_checksum = True,
                                  level = 14).compress(data)

    def pack_compress_cb(self, data):
        result = zstd.ZstdCompressor(write_content_size = True, write_checksum = True,
                                   level = 14).compress(msgpack.packb(data))
        return result

    def pack_compress_gen_cb(self, data):
        yield zstd.ZstdCompressor(write_content_size = True, write_checksum = True,
                                  level = 14).compress(msgpack.packb(data))

    def failed_cb(self, exc):
        print(exc)

    def result_cb(self, result):
        self.result.append(result)

    def results_cb(self, results):
        self.result.extend(results)

    def locked_result_future_cb(self, result):
        with self.lock:
            self.result.append(result.result())

    def map(self, data):
        pool = fastthreadpool.Pool()
        pool.map(self.worker, data)
        pool.shutdown()
        self.result = list(pool.done)

    def map_done_cb(self, data):
        pool = fastthreadpool.Pool(done_callback = self.result_cb)
        pool.map(self.worker, data)
        pool.shutdown()

    def map_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        pool.map(self.worker, data)
        pool.shutdown()
        self.result = list(pool.done)

    def imap(self, data):
        pool = fastthreadpool.Pool()
        pool.imap(self.worker_gen, data)
        pool.shutdown()
        self.result = list(pool.done)

    def imap_done_cb(self, data):
        pool = fastthreadpool.Pool(done_callback = self.result_cb)
        pool.imap(self.worker_gen, data)
        pool.shutdown()

    def imap_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        pool.imap(self.worker_gen, data)
        pool.shutdown()
        self.result = list(pool.done)

    def submit(self, data):
        pool = fastthreadpool.Pool()
        for value in data:
            pool.submit(self.worker, value)
        pool.shutdown()
        self.result = list(pool.done)

    def submit_done_cb(self, data):
        pool = fastthreadpool.Pool(done_callback = self.result_cb)
        for value in data:
            pool.submit(self.worker, value)
        pool.shutdown()

    def submit_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback = self.failed_cb)
        for value in data:
            pool.submit(self.worker, value)
        pool.shutdown()
        self.result = list(pool.done)

    def ThreadPool_map(self, data):
        pool = ThreadPool()
        results = pool.map(self.worker, data)
        pool.close()
        pool.join()
        self.result = results

    def ThreadPool_map_async_done_cb(self, data):
        pool = ThreadPool()
        pool.map_async(self.worker, data, callback = self.results_cb)
        pool.close()
        pool.join()

    def ThreadPool_apply_async_done_cb(self, data):
        pool = ThreadPool()
        for value in data:
            pool.apply_async(self.worker, ( value, ), callback = self.result_cb)
        pool.close()
        pool.join()

    def ThreadPoolExecutor_map(self, data):
        pool = ThreadPoolExecutor()
        results = pool.map(self.worker, data)
        pool.shutdown()
        self.result = list(results)

    def ThreadPoolExecutor_submit_done_cb(self, data):
        pool = ThreadPoolExecutor()
        for value in data:
            future = pool.submit(self.worker, value)
            future.add_done_callback(self.locked_result_future_cb)
        pool.shutdown()

    def test_compress(self, test_cb, data):
        self.result = []
        self.worker = self.compress_cb
        self.worker_gen = self.compress_gen_cb
        t = time.time()
        getattr(self, test_cb)(data)
        print("%6.3f %10d %s" % (time.time() - t, len(self.result), test_cb))

    def test_pack_compress(self, test_cb, data):
        self.result = []
        self.worker = self.pack_compress_cb
        self.worker_gen = self.pack_compress_gen_cb
        t = time.time()
        getattr(self, test_cb)(data)
        print("%6.3f %10d %s" % (time.time() - t, len(self.result), test_cb))

    def run_compress(self, n, cnt):
        packed_values = msgpack.packb(list(range(n)))
        print("\nCompress %d times %d values:" % (cnt, n))
        values = [ packed_values for _ in range(cnt) ]
        self.result = []
        t = time.time()
        for value in values:
            self.result_cb(self.compress_cb(value))
        print("%6.3f %10d single threaded" % (time.time() - t, len(self.result)))
        print("fastthreadpool:")
        self.test_compress("map", values)
        self.test_compress("map_done_cb", values)
        self.test_compress("map_failed_cb", values)
        self.test_compress("imap", values)
        self.test_compress("imap_done_cb", values)
        self.test_compress("imap_failed_cb", values)
        self.test_compress("submit", values)
        self.test_compress("submit_done_cb", values)
        self.test_compress("submit_failed_cb", values)
        print("multiprocessing.pool.ThreadPool:")
        self.test_compress("ThreadPool_map", values)
        self.test_compress("ThreadPool_map_async_done_cb", values)
        self.test_compress("ThreadPool_apply_async_done_cb", values)
        print("concurrent.futures.ThreadPoolExecutor:")
        self.test_compress("ThreadPoolExecutor_map", values)
        self.test_compress("ThreadPoolExecutor_submit_done_cb", values)

    def run_pack_compress(self, n, cnt):
        print("\nPack and compress %d times %d values:" % (cnt, n))
        values = [ list(range(n)) for _ in range(cnt) ]
        self.result = []
        t = time.time()
        for value in values:
            self.result_cb(self.pack_compress_cb(value))
        print("%6.3f %10d single threaded" % (time.time() - t, len(self.result)))
        print("fastthreadpool:")
        self.test_pack_compress("map", values)
        self.test_pack_compress("map_done_cb", values)
        self.test_pack_compress("map_failed_cb", values)
        self.test_pack_compress("imap", values)
        self.test_pack_compress("imap_done_cb", values)
        self.test_pack_compress("imap_failed_cb", values)
        self.test_pack_compress("submit", values)
        self.test_pack_compress("submit_done_cb", values)
        self.test_pack_compress("submit_failed_cb", values)
        print("multiprocessing.pool.ThreadPool:")
        self.test_pack_compress("ThreadPool_map", values)
        self.test_pack_compress("ThreadPool_map_async_done_cb", values)
        self.test_pack_compress("ThreadPool_apply_async_done_cb", values)
        print("concurrent.futures.ThreadPoolExecutor:")
        self.test_pack_compress("ThreadPoolExecutor_map", values)
        self.test_pack_compress("ThreadPoolExecutor_submit_done_cb", values)

    def run(self, n, cnt):
        self.run_compress(n, cnt)
        self.run_pack_compress(n, cnt)


if __name__ == "__main__":
    test = TestSemaphore()
    test.run(1000000)
    test = TestValues()
    test.run(1000000)
    test = TestLists()
    test.run(20000, 10000)
    test = TestCompress()
    test.run(1000, 10000)
