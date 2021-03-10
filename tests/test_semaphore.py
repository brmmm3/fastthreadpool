import threading
import fastthreadpool


class TestSemaphore(object):

    @staticmethod
    def acquire_cb(s):
        s.acquire()

    @staticmethod
    def release_cb(s):
        s.release()

    def test_fastthreadpool_Semaphore(self):
        s = fastthreadpool.Semaphore(8)
        for _ in range(10):
            s.acquire()
            assert s.value == 7
            s.acquire()
            assert s.value == 6
            s.release()
            assert s.value == 7
            s.release()
            assert s.value == 8
        assert s.value == 8

    # noinspection PyUnresolvedReferences
    def test_threading_Semaphore(self):
        s = threading.Semaphore(8)
        for _ in range(10):
            s.acquire()
            assert s._value == 7
            s.acquire()
            assert s._value == 6
            s.release()
            assert s._value == 7
            s.release()
            assert s._value == 8
        assert s._value == 8

    def test_fastthreadpool_Semaphore_threads(self):
        s = fastthreadpool.Semaphore(8)
        pool = fastthreadpool.Pool()
        for value in range(10):
            if value & 1:
                pool.submit(self.release_cb, s)
            else:
                pool.submit(self.acquire_cb, s)
        pool.shutdown()
        assert s.value == 8

    # noinspection PyUnresolvedReferences
    def test_threading_Semaphore_threads(self):
        s = threading.Semaphore(8)
        pool = fastthreadpool.Pool()
        for value in range(10):
            if value & 1:
                pool.submit(self.release_cb, s)
            else:
                pool.submit(self.acquire_cb, s)
        pool.shutdown()
        assert s._value == 8
