# Copyright 2018 Martin Bammer. All Rights Reserved.
# Licensed under MIT license.

"""Implements a lightweight and fast thread pool."""

__author__ = 'Martin Bammer (mrbm74@gmail.com)'

import sys
import atexit
import inspect
import time
import threading
import itertools
from collections import deque
if sys.version_info[0] > 2:
    import _thread
    from os import cpu_count
else:
    import thread as _thread
    from multiprocessing import cpu_count


# Create own semaphore class which is much faster than the original version in the
# threading module.
class Semaphore(object):

    def __init__(self):
        self._value = 0
        self._value_lock = _thread.allocate_lock()
        self._zero_lock = _thread.allocate_lock()
        self._zero_lock.acquire()

    def acquire(self):
        if self._value < 1:
            self._zero_lock.acquire()
        with self._value_lock:
            self._value -= 1

    def release(self):
        if self._zero_lock.locked():
            try:
                self._zero_lock.release()
            except:
                pass
        with self._value_lock:
            self._value += 1


_shutdown = False
_job_cnt = Semaphore()
_children = set()

LOGGER_NAME = 'fastthreadpool'
DEFAULT_LOGGING_FORMAT = '[%(levelname)s/%(processName)s] %(message)s'


def _python_exit():
    global _shutdown
    _shutdown = True
    _job_cnt.release()
    for thread in _children:
        thread.join()

atexit.register(_python_exit)


class Pool(object):

    def __init__(self, max_children = None, child_name_prefix = "", done_callback = None, failed_callback = None,
                 log_level = None):
        global _shutdown, _job_cnt
        _shutdown = False
        _job_cnt = Semaphore()
        self.max_children = None
        if max_children is None:
            self.max_children = cpu_count()
        elif max_children > 0:
            self.max_children = max_children
        else:
            self.max_children = cpu_count() + max_children
        if self.max_children <= 0:
            raise ValueError("Number of child threads must be greater than 0")
        self.child_name_prefix = child_name_prefix  + "-" if child_name_prefix else "ThreadPool%s-" % id(self)
        self._child_cnt = 0
        self.jobs = deque()
        self.done = deque()
        self.failed = deque()
        self._done_cnt = Semaphore()
        self._failed_cnt = Semaphore()
        self.logger = None
        if done_callback:
            self._thr_done = threading.Thread(target = self._done_thread, args = ( done_callback, ),
                                              name = "ThreadPoolDone")
            self._thr_done.daemon = True
            self._thr_done.start()
        if failed_callback or log_level:
            if log_level:
                import logging
                self.logger = logging.getLogger(LOGGER_NAME)
                self.logger.propagate = False
                formatter = logging.Formatter(DEFAULT_LOGGING_FORMAT)
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                if log_level:
                    self.logger.setLevel(log_level)
            self._thr_failed = threading.Thread(target = self._failed_thread, args = ( failed_callback, ),
                                                name = "ThreadPoolFailed")
            self._thr_failed.daemon = True
            self._thr_failed.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def _done_thread(self, done_callback):
        done_popleft = self.done.popleft
        _done_cnt_acquire = self._done_cnt.acquire
        while True:
            try:
                result = done_popleft()
            except:
                if _shutdown:
                    break
                _done_cnt_acquire()
            else:
                done_callback(result)

    def _failed_thread(self, failed_callback):
        failed_popleft = self.failed.popleft
        _failed_cnt_acquire = self._failed_cnt.acquire
        while True:
            try:
                thr_name, exc = failed_popleft()
            except:
                if _shutdown:
                    break
                _failed_cnt_acquire()
            else:
                if failed_callback is None:
                    self.logger.exception(exc)
                else:
                    failed_callback(exc)

    def _child(self):
        _job_cnt_acquire = _job_cnt.acquire
        _done_cnt = self._done_cnt
        _done_cnt_release = _done_cnt.release
        _failed_cnt = self._failed_cnt
        _failed_cnt_release = _failed_cnt.release
        done_append = self.done.append
        failed_append = self.failed.append
        jobs_popleft = self.jobs.popleft
        while True:
            try:
                job = jobs_popleft()
            except:
                # Locking is expensive. So only use it when needed.
                _job_cnt_acquire()
                continue
            if job is None or _shutdown:
                _job_cnt.release()
                break
            try:
                fn, done_callback, args, kwargs = job
                if done_callback is True:
                    if inspect.isgeneratorfunction(fn):
                        for result in fn(*args, **kwargs):
                            done_append(result)
                            if _done_cnt._value < 1:
                                _done_cnt_release()
                    else:
                        done_append(fn(*args, **kwargs))
                        if _done_cnt._value < 1:
                            _done_cnt_release()
                elif callable(done_callback):
                    if inspect.isgeneratorfunction(fn):
                        for result in fn(*args, **kwargs):
                            done_callback(result)
                    else:
                        done_callback(fn(*args, **kwargs))
            except Exception as exc:
                failed_append(exc)
                if _failed_cnt._value < 1:
                    _failed_cnt_release()

    def _submit(self, fn, done_callback, args, kwargs):
        if _shutdown:
            raise ValueError("Pool not running")
        if (self._child_cnt == 0) or ((self._child_cnt < self.max_children) and self.jobs):
            self._child_cnt += 1
            child = threading.Thread(target = self._child,
                                      name = self.child_name_prefix + str(self._child_cnt))
            child.daemon = True
            child.start()
            _children.add(child)
        self.jobs.append(( fn, done_callback, args, kwargs ))
        if _job_cnt._value < 1:
            # Locking is expensive. So only use it when needed.
            _job_cnt.release()

    def submit(self, fn, *args, **kwargs):
        self._submit(fn, True, args, kwargs)

    def submit_done(self, fn, done_callback, *args, **kwargs):
        self._submit(fn, done_callback, args, kwargs)

    def _map_child(self, fn, itr, done_append):
        _done_cnt = self._done_cnt
        _done_cnt_release = _done_cnt.release
        _failed_cnt = self._failed_cnt
        _failed_cnt_release = _failed_cnt.release
        _done_append = self.done.append
        failed_append = self.failed.append
        if hasattr(self, "_thr_done"):
            if done_append:
                for args in itr:
                    if _shutdown:
                        break
                    try:
                        _done_append(fn(args))
                        if _done_cnt._value < 1:
                            _done_cnt_release()
                    except Exception as exc:
                        failed_append(exc)
                        if _failed_cnt._value < 1:
                            _failed_cnt_release()
            else:
                for args in itr:
                    if _shutdown:
                        break
                    try:
                        fn(args)
                    except Exception as exc:
                        failed_append(exc)
                        if _failed_cnt._value < 1:
                            _failed_cnt_release()
        elif done_append:
            for args in itr:
                if _shutdown:
                    break
                try:
                    _done_append(fn(args))
                except Exception as exc:
                    failed_append(exc)
                    if _failed_cnt._value < 1:
                        _failed_cnt_release()
        else:
            for args in itr:
                if _shutdown:
                    break
                try:
                    fn(args)
                except Exception as exc:
                    failed_append(exc)
                    if _failed_cnt._value < 1:
                        _failed_cnt_release()

    def _imap_child(self, fn, itr, done_append):
        _done_cnt = self._done_cnt
        _done_cnt_release = _done_cnt.release
        _failed_cnt = self._failed_cnt
        _failed_cnt_release = _failed_cnt.release
        _done_append = self.done.append
        failed_append = self.failed.append
        if hasattr(self, "_thr_done"):
            for args in itr:
                if _shutdown:
                    break
                try:
                    for result in fn(args):
                        _done_append(result)
                        if _done_cnt._value < 1:
                            _done_cnt_release()
                except Exception as exc:
                    failed_append(exc)
                    if _failed_cnt._value < 1:
                        _failed_cnt_release()
        else:
            for args in itr:
                if _shutdown:
                    break
                try:
                    for result in fn(args):
                        _done_append(result)
                except Exception as exc:
                    failed_append(exc)
                    if _failed_cnt._value < 1:
                        _failed_cnt_release()

    def map(self, fn, itr, done_append = True, shutdown_timeout = None):
        if _shutdown:
            raise ValueError("Pool not running")
        chunksize, extra = divmod(len(itr), self.max_children)
        if extra:
            chunksize += 1
        it = iter(itr)
        child = self._imap_child if inspect.isgeneratorfunction(fn) else self._map_child
        for _ in range(self.max_children):
            self._child_cnt += 1
            thread = threading.Thread(target = child, args = ( fn, itertools.islice(it, chunksize), done_append ),
                                      name = self.child_name_prefix + str(self._child_cnt))
            thread.daemon = True
            thread.start()
            _children.add(thread)
        if not shutdown_timeout is None:
            self.shutdown(shutdown_timeout)

    def _join_thread(self, thread, t, timeout):
        global _shutdown
        dt = 0.1 if timeout is None else t - time.time()
        while True:
            try:
                thread.join(dt)
                if not thread.is_alive():
                    return
                if not timeout is None:
                    raise TimeoutError("Failed to join thread %s" % thread.name)
            except KeyboardInterrupt:
                _shutdown = True
                raise
            except:
                pass

    def shutdown(self, timeout = None):
        global _shutdown
        for _ in range(self.max_children):
            self.jobs.append(None)
        _job_cnt.release()
        t = None if timeout is None else time.time() + timeout
        for thread in _children:
            self._join_thread(thread, t, timeout)
        _children.clear()
        if hasattr(self, "_thr_done"):
            _shutdown = True
            self._done_cnt.release()
            self._join_thread(self._thr_done, t, timeout)
        if hasattr(self, "_thr_failed"):
            _shutdown = True
            self._failed_cnt.release()
            self._join_thread(self._thr_failed, t, timeout)

    def cancel(self):
        global _shutdown
        _shutdown = True
        for _ in range(self.max_children):
            self.jobs.appendleft(None)
        _job_cnt.release()
