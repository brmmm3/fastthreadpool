# Copyright 2018 Martin Bammer. All Rights Reserved.
# Licensed under MIT license.
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
#cython: cdivision=True
#cython: optimize.use_switch=True
#cython: optimize.unpack_method_calls=False
#cython: unraisable_tracebacks=True

"""Implements a lightweight and fast thread pool."""

__author__ = 'Martin Bammer (mrbm74@gmail.com)'

#c cdef sys, isgeneratorfunction, Lock, Thread, Timer, islice, deque, _time, sleep, cpu_count
import sys
import atexit
from inspect import isgeneratorfunction
from threading import Lock, Thread, Timer
from itertools import islice
from time import sleep, mktime, struct_time
try:
    from time import monotonic as _time
except ImportError:
    from time import time as _time
from collections import deque
if sys.version_info[0] > 2:
    from os import cpu_count
else:
    from multiprocessing import cpu_count

if sys.version_info[0] < 3:
    class TimeoutError(Exception):
        pass


class PoolCallback(Exception):
    pass


class PoolStopped(Exception):
    pass


#c cdef set _pools
_pools = set()

LOGGER_NAME = 'fastthreadpool'
DEFAULT_LOGGING_FORMAT = '[%(levelname)s/%(processName)s] %(message)s'


def shutdown(now=True):
    for pool in _pools:
        if now:
            pool.shutdown_children()
            pool.cancel(None, True)
            pool.shutdown(None, True)
        else:
            pool.cancel(None, False)
            pool.shutdown()


atexit.register(shutdown)

#c from cpython cimport pythread
#c from cpython.exc cimport PyErr_NoMemory


#c cdef class Condition:
class Condition:  #p
    #c cdef pythread.PyThread_type_lock _lock
    #c cdef object _waiters
    #c cdef object _waiters_append
    #c cdef object _waiters_remove
    #c cdef object _waiters_popleft

    #c def __cinit__(self):
    def __init__(self):  #p
        #c self._lock = pythread.PyThread_allocate_lock()
        #c if self._lock is NULL:
        #c     PyErr_NoMemory()
        self._lock = Lock()  #p
        self._waiters = deque()
        self._waiters_append = self._waiters.append
        self._waiters_remove = self._waiters.remove
        self._waiters_popleft = self._waiters.popleft

    #c def __dealloc__(self):
    #c     if self._lock:
    #c         pythread.PyThread_free_lock(self._lock)
    #c         self._lock = NULL

    #c cdef bint _is_owned(self):
    def _is_owned(self):  #p
        #c if pythread.PyThread_acquire_lock(self._lock, 0):
        if self._lock.acquire(False):  #p
            #c pythread.PyThread_release_lock(self._lock)
            self._lock.release()  #p
            return False
        return True

    #c cdef void acquire(self):
    def acquire(self):  #p
        #c pythread.PyThread_acquire_lock(self._lock, 1)
        self._lock.acquire()  #p

    #c cdef void release(self):
    def release(self):  #p
        #c pythread.PyThread_release_lock(self._lock)
        self._lock.release()  #p

    #c cdef bint wait(self) except +:
    def wait(self):  #p
        if not self._is_owned():
            raise RuntimeError("cannot wait on un-acquired lock")
        waiter = Lock()
        waiter.acquire()
        self._waiters_append(waiter)
        #c pythread.PyThread_release_lock(self._lock)
        self._lock.release()  #p
        gotit = False
        try:
            waiter.acquire()
            gotit = True
            return gotit
        finally:
            #c pythread.PyThread_acquire_lock(self._lock, 1)
            self._lock.acquire()  #p
            if not gotit:
                try:
                    self._waiters_remove(waiter)
                except ValueError:
                    pass

    #c cdef void notify(self) except +:
    def notify(self):  #p
        if not self._is_owned():
            raise RuntimeError("cannot notify on un-acquired lock")
        if self._waiters:
            self._waiters_popleft().release()


#c cdef class Semaphore:
class Semaphore:  #p
    #c cdef Condition _cond
    #c cdef int _value

    #c def __cinit__(self, int value=1):
    def __init__(self, value=1):  #p
        if value < 0:
            raise ValueError("semaphore initial value must be >= 0")
        self._cond = Condition()
        self._value = value

    @property
    def value(self):
        return self._value

    #c cpdef bint acquire(self, bint blocking=True):
    def acquire(self, blocking=True):  #p
        rc = False
        self._cond.acquire()
        while self._value == 0:
            if not blocking:
                break
            self._cond.wait()
        else:
            self._value -= 1
            rc = True
        self._cond.release()
        return rc

    #c cpdef void release(self):
    def release(self):  #p
        self._cond.acquire()
        self._value += 1
        self._cond.notify()
        self._cond.release()


class TimerObj(object):

    def __init__(self):
        self.old_timer_id = None   # Old timer id
        self.timer_id = None


#c cdef class Pool:
class Pool(object):  #p

    #c cdef Semaphore _job_cnt
    #c cdef set children
    #c cdef int max_children
    #c cdef str child_name_prefix
    #c cdef bint result_id
    #c cdef int _child_cnt, _busy_cnt
    #c cdef pythread.PyThread_type_lock _busy_lock
    #c cdef object _delayed, _scheduled, _jobs, _jobs_append, _jobs_appendleft, _done, _failed
    #c cdef Semaphore _done_cnt, _failed_cnt
    #c cdef bint _shutdown, _shutdown_children
    #c cdef object logger
    #c cdef object init_callback
    #c cdef object _thr_done, _thr_failed

    #c def __cinit__(self, int max_children=-9999, str child_name_prefix="", init_callback=None,
    #c               done_callback=None, failed_callback=None, int log_level=0, bint result_id=False):
    def __init__(self, max_children=-9999, child_name_prefix="", init_callback=None,  #p
                 done_callback=None, failed_callback=None, log_level=None, result_id=False):  #p
        self._job_cnt = Semaphore()
        self.children = set()
        if max_children <= -9999:
            self.max_children = cpu_count()
        elif max_children > 0:
            self.max_children = max_children
        else:
            self.max_children = cpu_count() + max_children
        if self.max_children <= 0:
            raise ValueError("Number of child threads must be greater than 0")
        self.child_name_prefix = child_name_prefix + "-" if child_name_prefix else "ThreadPool%s-" % id(self)
        self.result_id = result_id
        self._child_cnt = 0
        #c self._busy_lock = pythread.PyThread_allocate_lock()
        self._busy_lock = Lock()  #p
        self._busy_cnt = 0
        self._delayed = deque()
        self._scheduled = deque()
        self._jobs = deque()
        self._jobs_append = self._jobs.append
        self._jobs_appendleft = self._jobs.appendleft
        self._done = deque()
        self._failed = deque()
        self._done_cnt = Semaphore(0)
        self._failed_cnt = Semaphore(0)
        self._shutdown_children = False
        self._shutdown = False
        self.logger = None
        self.init_callback = init_callback
        if done_callback:
            self._thr_done = Thread(target=self._done_thread, args=(done_callback, ),
                                    name="ThreadPoolDone")
            self._thr_done.daemon = True
            self._thr_done.start()
        else:
            self._thr_done = None
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
            self._thr_failed = Thread(target=self._failed_thread, args=(failed_callback, ),
                                      name="ThreadPoolFailed")
            self._thr_failed.daemon = True
            self._thr_failed.start()
        else:
            self._thr_failed = None
        _pools.add(self)

    def __del__(self):
        #c pythread.PyThread_free_lock(self._busy_lock)
        if _pools:
            _pools.remove(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    #c cdef void _busy_lock_inc(self):
    def _busy_lock_inc(self):  #p
        #c pythread.PyThread_acquire_lock(self._busy_lock, 1)
        self._busy_lock.acquire()  #p
        self._busy_cnt += 1
        #c pythread.PyThread_release_lock(self._busy_lock)
        self._busy_lock.release()  #p

    #c cdef void _busy_lock_dec(self):
    def _busy_lock_dec(self):  #p
        #c pythread.PyThread_acquire_lock(self._busy_lock, 1)
        self._busy_lock.acquire()  #p
        self._busy_cnt -= 1
        #c pythread.PyThread_release_lock(self._busy_lock)
        self._busy_lock.release()  #p

    def _done_thread(self, done_callback):
        done_popleft = self._done.popleft
        while True:
            try:
                while True:
                    done_callback(done_popleft())
            except:
                if self._shutdown:
                    break
                self._done_cnt.acquire()

    def _failed_thread(self, failed_callback):
        failed_popleft = self._failed.popleft
        logger_exception = None if self.logger is None else self.logger.exception
        while True:
            try:
                if failed_callback is None:
                    if logger_exception is None:
                        while True:
                            failed_popleft()
                    else:
                        while True:
                            logger_exception(failed_popleft()[1])
                else:
                    while True:
                        failed_callback(failed_popleft()[1])
            except:
                if self._shutdown:
                    break
                self._failed_cnt.acquire()

    def _child(self):
        #c cdef bint run_child, pop_failed
        self._busy_lock_inc()
        child_busy = True
        _done_append = self._done.append
        failed_append = self._failed.append
        jobs_popleft = self._jobs.popleft
        run_child = True
        pop_failed = False
        while run_child:
            try:
                while True:
                    if not child_busy:
                        self._busy_lock_inc()
                        child_busy = True
                    pop_failed = True
                    job = jobs_popleft()
                    pop_failed = False
                    if job is None or self._shutdown_children:
                        self._job_cnt.release()
                        run_child = False
                        break
                    fn, done_callback, args, kwargs = job
                    if done_callback is False:
                        if isgeneratorfunction(fn):
                            for _ in fn(*args, **kwargs):
                                pass
                        else:
                            fn(*args, **kwargs)
                    elif done_callback is True:
                        if isgeneratorfunction(fn):
                            jobid = id(job)
                            for result in fn(*args, **kwargs):
                                if self.result_id:
                                    _done_append((jobid, result))
                                else:
                                    _done_append(result)
                                self._done_cnt.release()
                        else:
                            if self.result_id:
                                _done_append((id(job), fn(*args, **kwargs)))
                            else:
                                _done_append(fn(*args, **kwargs))
                            self._done_cnt.release()
                    elif callable(done_callback):
                        if isgeneratorfunction(fn):
                            for result in fn(*args, **kwargs):
                                done_callback(result)
                        else:
                            done_callback(fn(*args, **kwargs))
            except Exception as exc:
                if self._shutdown_children:
                    self._job_cnt.release()
                    break
                if pop_failed:
                    self._busy_lock_dec()
                    child_busy = False
                    self._job_cnt.acquire()
                else:
                    if self.result_id:
                        failed_append((id(job), exc))
                    else:
                        failed_append(exc)
                    self._failed_cnt.release()
        self._busy_lock_dec()

    #c cdef object _submit(self, fn, done_callback, args, kwargs, bint high_priority) except +:
    def _submit(self, fn, done_callback, args, kwargs, high_priority):  #p
        if self._shutdown_children:
            raise PoolStopped("Pool not running")
        if (self._busy_cnt >= self._child_cnt) and (self._child_cnt < self.max_children):
            self._child_cnt += 1
            thr_child = Thread(target=self._child,
                               name=self.child_name_prefix + str(self._child_cnt))
            thr_child.daemon = True
            if self.init_callback is not None:
                self.init_callback(thr_child)
            thr_child.start()
            self.children.add(thr_child)
        job = (fn, done_callback, args, kwargs)
        if high_priority:
            self._jobs_appendleft(job)
        else:
            self._jobs_append(job)
        self._job_cnt.release()
        if self.result_id:
            return id(job)
        return None

    def submit(self, fn, *args, **kwargs):
        return self._submit(fn, True, args, kwargs, False)

    def submit_done(self, fn, done_callback, *args, **kwargs):
        return self._submit(fn, done_callback, args, kwargs, False)

    def submit_first(self, fn, *args, **kwargs):
        return self._submit(fn, True, args, kwargs, True)

    def submit_done_first(self, fn, done_callback, *args, **kwargs):
        return self._submit(fn, done_callback, args, kwargs, True)

    def _submit_later_do(self, timer_obj, fn, done_callback, args, kwargs):
        self._submit(fn, done_callback, args, kwargs, True)
        self._delayed.remove(timer_obj[0])

    #c cdef object _submit_later(self, delay, fn, done_callback, args, kwargs) except +:
    def _submit_later(self, delay, fn, done_callback, args, kwargs):  #p
        timer_obj = [None]
        timer = Timer(delay, self._submit_later_do, (timer_obj, fn, done_callback, args, kwargs))
        timer_obj[0] = timer
        timer.start()
        self._delayed.append(timer)
        return timer

    def submit_later(self, delay, fn, *args, **kwargs):
        return self._submit_later(delay, fn, True, args, kwargs)

    def submit_done_later(self, delay, fn, done_callback, *args, **kwargs):
        return self._submit_later(delay, fn, done_callback, args, kwargs)

    #c cdef object _submit_at(self, _runat, interval, fn, done_callback, args, kwargs) except +:
    def _submit_at(self, _runat, interval, fn, done_callback, args, kwargs):  #p
        if isinstance(_runat, struct_time):
            _runat = mktime(_runat)
        now = _time()
        if _runat < now:
            raise ValueError("_runat has invalid value!")
        timer_obj = TimerObj()
        timer = Timer(_runat - now, self._schedule_do, (timer_obj, _runat - interval, interval,
                                                        fn, done_callback, args, kwargs))
        timer_obj.timer_id = timer
        self._scheduled.append(timer)
        timer.start()
        return timer_obj

    def submit_at(self, _runat, interval, fn, *args, **kwargs):
        return self._submit_at(_runat, interval, fn, True, args, kwargs)

    def submit_done_at(self, _runat, interval, fn, done_callback, *args, **kwargs):
        return self._submit_at(_runat, interval, fn, done_callback, args, kwargs)

    @property
    def delayed(self):
        return self._delayed

    def _schedule_do(self, timer_obj, _runat, interval, fn, done_callback, args, kwargs):
        self._submit(fn, done_callback, args, kwargs, True)
        self._scheduled.remove(timer_obj.timer_id)
        if interval <= 0.0:
            return
        now = _time()
        dt = interval - (now - _runat - interval)
        timer = Timer(dt, self._schedule_do, (timer_obj, now, interval, fn,
                                              done_callback, args, kwargs))
        timer_obj.old_timer_id = timer_obj.timer_id
        timer_obj.timer_id = timer
        self._scheduled.append(timer)
        timer.start()

    #c cdef object _schedule(self, interval, fn, done_callback, args, kwargs):
    def _schedule(self, interval, fn, done_callback, args, kwargs):  #p
        timer_obj = TimerObj()
        timer = Timer(interval, self._schedule_do, (timer_obj, _time(), interval,
                                                    fn, done_callback, args, kwargs))
        timer_obj.timer_id = timer
        self._scheduled.append(timer)
        timer.start()
        return timer_obj

    def schedule(self, interval, fn, *args, **kwargs):
        return self._schedule(interval, fn, True, args, kwargs)

    def schedule_done(self, interval, fn, done_callback, *args, **kwargs):
        return self._schedule(interval, fn, done_callback, args, kwargs)

    @property
    def scheduled(self):
        return self._scheduled

    def as_completed(self, wait=None):
        #c cdef float to
        #c cdef object pyto
        #c cdef bint do_sleep
        if self._thr_done is not None:
            raise PoolCallback("Using done_callback!")
        if self._thr_failed is not None:
            raise PoolCallback("Using failed_callback!")
        if wait is not False and isinstance(wait, (int, float)):
            pyto = _time() + wait
            to = pyto
        else:
            to = pyto = 0.0
        done = self._done
        failed = self._failed
        done_popleft = done.popleft
        failed_popleft = failed.popleft
        while self._busy_cnt or self._jobs:
            do_sleep = True
            while done:
                yield done_popleft()
                do_sleep = False
            while failed:
                yield failed_popleft()
                do_sleep = False
            if wait is False or ((to > 0.0) and (_time() > pyto)):
                return
            if do_sleep:
                sleep(0.01)

    #c def _map_child(self, fn, itr, done_callback):
    def _map_child(self, fn, itr, done_callback):  #p
        #c cdef bint append_done
        self._busy_lock_inc()
        _done_append = self._done.append
        _failed_append = self._failed.append
        if done_callback is False:
            for args in itr:
                if self._shutdown_children:
                    break
                try:
                    fn(args)
                except Exception as exc:
                    _failed_append(exc)
                    self._failed_cnt.release()
        elif done_callback is True:
            for args in itr:
                if self._shutdown_children:
                    break
                try:
                    _done_append(fn(args))
                    self._done_cnt.release()
                except Exception as exc:
                    _failed_append(exc)
                    self._failed_cnt.release()
        elif callable(done_callback):
            for args in itr:
                if self._shutdown_children:
                    break
                try:
                    done_callback(fn(args))
                except Exception as exc:
                    _failed_append(exc)
                    self._failed_cnt.release()
        self._busy_lock_dec()

    #c def _imap_child(self, fn, itr, done_callback):
    def _imap_child(self, fn, itr, done_callback):  #p
        #c cdef bint append_done
        self._busy_lock_inc()
        _done_append = self._done.append
        _failed_append = self._failed.append
        if done_callback is False:
            for args in itr:
                if self._shutdown_children:
                    break
                try:
                    for _ in fn(args):
                        pass
                except Exception as exc:
                    _failed_append(exc)
                    self._failed_cnt.release()
        elif done_callback is True:
            for args in itr:
                if self._shutdown_children:
                    break
                try:
                    for result in fn(args):
                        _done_append(result)
                        self._done_cnt.release()
                except Exception as exc:
                    _failed_append(exc)
                    self._failed_cnt.release()
        elif callable(done_callback):
            for args in itr:
                if self._shutdown_children:
                    break
                try:
                    for result in fn(args):
                        done_callback(result)
                except Exception as exc:
                    _failed_append(exc)
                    self._failed_cnt.release()
        self._busy_lock_dec()

    def map(self, fn, itr, done_callback=True):
        #c cdef int itr_cnt, chunksize
        #c cdef object pychunksize
        if self._shutdown_children:
            raise PoolStopped("Pool not running")
        for child in tuple(self.children):
            if not child.is_alive():
                self.children.remove(child)
        itr_cnt = len(itr)
        chunksize = itr_cnt // self.max_children
        if itr_cnt % self.max_children:
            pychunksize = chunksize + 1
        else:
            pychunksize = chunksize
        it = iter(itr)
        cb_child = self._imap_child if isgeneratorfunction(fn) else self._map_child
        for _ in range(self.max_children):
            self._child_cnt += 1
            thr_child = Thread(target=cb_child, args=(fn, islice(it, pychunksize), done_callback),
                               name=self.child_name_prefix + str(self._child_cnt))
            thr_child.daemon = True
            if self.init_callback is not None:
                self.init_callback(thr_child)
            thr_child.start()
            self.children.add(thr_child)

    def clear(self):
        self._shutdown_children = False
        self._jobs.clear()
        self._done.clear()
        self._done_cnt = Semaphore(0)
        self._failed.clear()
        self._failed_cnt = Semaphore(0)

    @property
    def alive(self):
        return len([1 for child in self.children if child.is_alive()])

    @property
    def busy(self):
        return self._busy_cnt

    @property
    def pending(self):
        return self._busy_cnt + len(self._jobs)

    @property
    def jobs(self):
        return self._jobs

    @property
    def done(self):
        return self._done

    @property
    def done_cnt(self):
        return self._done_cnt

    @property
    def failed(self):
        return self._failed

    @property
    def failed_cnt(self):
        return self._failed_cnt

    def _join_thread(self, thread, t, timeout):
        dt = None if timeout is None else max(t - _time(), 0.0)
        while True:
            try:
                thread.join(dt)
                if not thread.is_alive():
                    return thread
                if timeout <= 0.0:
                    return None
                if timeout is not None:
                    raise TimeoutError("Failed to join thread %s" % thread.name)
            except KeyboardInterrupt:
                self._shutdown_children = True
                self._shutdown = True
                raise

    def shutdown_children(self):
        self._shutdown_children = True
        self._job_cnt.release()

    def shutdown(self, timeout=None, soon=False):
        for _ in self.children:
            if soon:
                self._jobs.appendleft(None)
            else:
                self._jobs_append(None)
        self._job_cnt.release()
        t = None if timeout is None else _time() + timeout
        for thread in tuple(self.children):
            self.children.discard(self._join_thread(thread, t, timeout))
        if t is not None and (_time() > t):
            self._delayed_cancel()
        if self.children:
            return False
        self._shutdown = True
        if self._thr_done is not None:
            self._done_cnt.release()
            self._join_thread(self._thr_done, t, timeout)
        if self._thr_failed is not None:
            self._failed_cnt.release()
            self._join_thread(self._thr_failed, t, timeout)
        return True

    def join(self, timeout=None):
        return self.shutdown(timeout, False)

    #c cdef void _delayed_cancel(self):
    def _delayed_cancel(self):  #p
        for timer in self._delayed:
            timer.cancel()
        self._delayed.clear()

    #c cdef void _scheduled_cancel(self):
    def _scheduled_cancel(self):  #p
        for timer in self._scheduled:
            timer.cancel()
        self._scheduled.clear()

    def cancel(self, job_id=None, timer=None):
        if timer is True:
            self._delayed_cancel()
            self._scheduled_cancel()
        elif isinstance(timer, TimerObj):
            try:
                timer.timer_id.cancel()
                self._scheduled.remove(timer.timer_id)
            except ValueError:
                pass
            try:
                timer.old_timer_id.cancel()
                self._scheduled.remove(timer.old_timer_id)
            except ValueError:
                pass
        elif timer is not None:
            timer.cancel()
            try:
                self._delayed.remove(timer)
            except ValueError:
                pass
            try:
                self._scheduled.remove(timer)
            except ValueError:
                pass
        if job_id is False:
            return True
        if job_id is None:
            self._jobs.clear()
            return True
        for job in self._jobs:
            if id(job) == job_id:
                try:
                    self._jobs.remove(job)
                    return True
                except ValueError:
                    return False
        return False
