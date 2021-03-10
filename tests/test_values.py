import os
import sys
import time
#import fastthreadpool
import fastthreadpool.fastthreadpool
from multiprocessing.pool import ThreadPool
if sys.version_info[0] > 2:
    from concurrent.futures import ThreadPoolExecutor


class TestValues(object):

    @staticmethod
    def worker_cb(data):
        return data

    @staticmethod
    def worker_gen_cb(data):
        yield data

    def failed_cb(self, exc):
        self.failed.append(exc)

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

    def test_fastthreadpool_map(self):
        data = list(range(10))
        pool = fastthreadpool.Pool()
        pool.map(self.worker_cb, data, unpack_args=False)
        pool.shutdown()
        assert data == list(pool.done)

    def test_map_no_done(self):
        data = list(range(10))
        pool = fastthreadpool.Pool()
        pool.map(self.worker_cb, data, done_callback=False, unpack_args=False)
        pool.shutdown()
        assert not pool.done
        assert not pool.failed

    def test_map_done(self):
        data = list(range(10))
        self.result = 0
        with fastthreadpool.Pool(done_callback=self.result_cb) as pool:
            pool.map(self.worker_cb, data)
        assert self.result == sum(data)

    def test_map_failed(self):
        data = list(range(10))
        self.failed = []
        pool = fastthreadpool.Pool(failed_callback=self.failed_cb)
        pool.map(self.worker_cb, data, unpack_args=True)  # Unpacking of int is not possible
        pool.shutdown()
        assert not pool.done
        assert not pool.failed
        assert len(self.failed) == len(data)
        assert self.failed[0].args[0] == "worker_cb() argument after * must be an iterable, not int"

    def test_map_gen(self):
        data = list(range(10))
        pool = fastthreadpool.Pool()
        pool.map(self.worker_gen_cb, data)
        pool.shutdown()
        assert not pool.failed
        assert len(pool.done) == len(data)
        assert sum(pool.done) == sum(data)

    def test_map_gen_done_no_result(self):
        data = list(range(10))
        with fastthreadpool.Pool(done_callback=self.result_cb) as pool:
            pool.map(self.worker_gen_cb, data)
        assert not pool.done
        assert len(pool.failed) == len(data)
        assert pool.failed.popleft().args[0] == "'TestValues' object has no attribute 'result'"

    def test_map_gen_done(self):
        data = list(range(10))
        self.result = 0
        with fastthreadpool.Pool(done_callback=self.result_cb) as pool:
            pool.map(self.worker_gen_cb, data)
        assert not pool.done
        assert not pool.failed
        assert self.result == 45

    def test_map_gen_failed(self):
        data = list(range(10))
        self.failed = []
        pool = fastthreadpool.Pool(failed_callback=self.failed_cb)
        pool.map(self.worker_gen_cb, data, unpack_args=True)  # Unpacking of int is not possible
        pool.shutdown()
        assert not pool.done
        assert not pool.failed
        assert len(self.failed) == len(data)
        assert self.failed[0].args[0] == "worker_gen_cb() argument after * must be an iterable, not int"

    def test_submit(self):
        data = list(range(10))
        pool = fastthreadpool.Pool()
        for value in data:
            pool.submit(self.worker_cb, value)
        pool.shutdown()
        assert not pool.failed
        assert len(pool.done) == 10
        assert sum(pool.done) == sum(data)

    def test_submit_result_id(self):
        data = list(range(10))
        pool = fastthreadpool.Pool(result_id=True)
        for value in data:
            pool.submit(self.worker_cb, value)
        pool.shutdown()
        assert not pool.failed
        assert len(pool.done) == 10
        assert sum([result[1] for result in pool.done]) == sum(data)

    def test_submit_gen(self):
        data = list(range(10))
        pool = fastthreadpool.Pool()
        for value in data:
            pool.submit(self.worker_gen_cb, value)
        pool.shutdown()
        assert not pool.failed
        assert len(pool.done) == 10
        assert sum(pool.done) == sum(data)

    def test_submit_gen_result_id(self):
        data = list(range(10))
        pool = fastthreadpool.Pool(result_id=True)
        for value in data:
            pool.submit(self.worker_gen_cb, value)
        pool.shutdown()
        assert not pool.failed
        assert len(pool.done) == 10
        assert sum([result[1] for result in pool.done]) == sum(data)

    def test_submit_pool_done(self):
        data = list(range(10))
        self.result = 0
        fastthreadpool.fastthreadpool.DBG.clear()
        with fastthreadpool.Pool(done_callback=self.result_cb) as pool:
            for value in data:
                pool.submit(self.worker_cb, value)
        assert not pool.failed
        assert len(pool.done) == 10
        assert sum(pool.done) == sum(data)

    def test_submit_gen_pool_done(self):
        data = list(range(10))
        with fastthreadpool.Pool(done_callback=self.result_cb) as pool:
            for value in data:
                pool.submit(self.worker_gen_cb, value)
        pass

    def submit_pool_failed_cb(self, data):
        pool = fastthreadpool.Pool(failed_callback=self.failed_cb)
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
        pool.map_async(self.worker, data, callback=self.results_cb)
        pool.close()
        pool.join()

    def ThreadPool_apply_async_done_cb(self, data):
        pool = ThreadPool()
        for value in data:
            pool.apply_async(self.worker, (value, ), callback=self.result_cb)
        pool.close()
        pool.join()

    def ThreadPoolExecutor_map(self, data):
        pool = ThreadPoolExecutor(max_workers=os.cpu_count())
        results = pool.map(self.worker, data)
        pool.shutdown()
        self.result = sum(results)

    def ThreadPoolExecutor_submit_done_cb(self, data):
        # Important: The result function is executed in the worker thread. So we need a
        #   lock in the result function!
        pool = ThreadPoolExecutor(max_workers=os.cpu_count())
        for value in data:
            future = pool.submit(self.worker, value)
            future.add_done_callback(self.locked_result_future_cb)
        pool.shutdown()

    def test(self, _test_cb, _data):
        self.result = 0
        self.worker = self.worker_cb
        self.worker_gen = self.worker_gen_cb
        #getattr(self, test_cb)(data)

    def run(self, cnt):
        print("\n%d values:" % cnt)
        values = list(range(cnt))
        self.result = 0
        t = time.time()
        for value in values:
            self.result_cb(self.worker_cb(value))
        print("%7.3f %12d single threaded" % (time.time() - t, self.result))
        t = time.time()
        self.result = sum([self.worker_cb(value) for value in values])
        print("%7.3f %12d sum list" % (time.time() - t, self.result))
        print("fastthreadpool:")
        self.test("map", values)
        self.test("map_no_done", values)
        self.test("map_done_cb", values)
        self.test("map_failed_cb", values)
        self.test("map_gen", values)
        self.test("map_gen_done_cb", values)
        self.test("map_gen_failed_cb", values)
        self.test("submit", values)
        self.test("submit_result_id", values)
        self.test("submit_gen", values)
        self.test("submit_gen_result_id", values)
        self.test("submit_pool_done_cb", values)
        self.test("submit_gen_pool_done_cb", values)
        self.test("submit_pool_failed_cb", values)
        self.test("submit_done_cb", values)
        print("multiprocessing.pool.ThreadPool:")
        self.test("ThreadPool_map", values)
        self.test("ThreadPool_map_async_done_cb", values)
        self.test("ThreadPool_apply_async_done_cb", values)
        if sys.version_info[0] > 2:
            print("concurrent.futures.ThreadPoolExecutor:")
            self.test("ThreadPoolExecutor_map", values)
            self.test("ThreadPoolExecutor_submit_done_cb", values)
