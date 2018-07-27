An efficient and lightweight thread pool
========================================

Existing implementations of thread pools have a relatively high overhead in certain
situations. Especially ``apply_async`` in ``multiprocessing.pool.ThreadPool`` and
``concurrent.futures.ThreadPoolExecutor`` at all (see benchmarks).
In case of ``ThreadPoolExecutor`` don't use the ``wait``. It can be *extremely* slow!
If you've only a small number of jobs and the jobs have a relatively long processing
time, then these overheads don't count. But in case of high number of jobs with
short processing time the overhead of the above implementations will noticeably
slow down the processing speed.
The fastthreadpool module solves this issue, because it has a very small overhead in
all situations.

**API**
=======

``Pool(max_children=-9999, child_name_prefix="", init_callback=None, done_callback=None, failed_callback=None, log_level=None, result_id=False)``
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

A thread pool object which controls a pool of worker threads to which jobs can be submitted. It supports asynchronous results with optional callbacks, submitting jobs with delayed execution, scheduling jobs with a repeating interval and has a parallel map implementation.

 - Child callback functions can also be generator functions.
 - Pool also supports the context management protocol.
 - Results with successful execution are saved in **done** queue.
 - Results with failed execution are saved in the **failed** queue.

 **max_children** defines the maximum number of child threads. If the value is equal or less than the default value the maximum number of child threads is the number of CPU cores. If the value is greater than 0 then it defines the absolute maximum number of child threads. If the value is equal or less than 0 then the maximum number of child threads is the number of CPU cores plus the parameter value. Child threads are only created on demand.

 **child_name_prefix** if set the child threads get this prefix for their names. If omitted the default prefix is `ThreadPool`.

 **init_callback** if set it is called with the new thread object as parameter before the thread is started.

 **done_callback** if defined for every result this callback function is called. It is important to know that the callback function is executed in it's *own single thread context*. If a done_callback is supplied in `submit_done` or `map` then this callback function is called for every result in the *same thread context as the worker thread*.

 **failed_callback** if defined for every failed execution of the worker functions the callback function is called. It is important to know that the callback function is executed in it's *own single thread context*.

 **log_level** if defined for every failed execution of the worker functions the exception is logged.

 **result_id** if *True* every result is a tuple with the result id in the first entry and the result value in the second entry.

``submit(fn, *args, **kwargs)``
*******************************

Submit a single job to the pool. **fn** is the function to call and **args** and **kwargs** the arguments. The job will be added to the **end** of the job queue.

The return value is an id which is the same as the first entry in the result if result_id is set. If the job needs to be removed from the queue this id has to be supplied to the cancel function.

``submit_done(fn, done_callback, *args, **kwargs)``
***************************************************

The same as **submit** but with an individual done callback function.

If **done_callback** is **True** then the results of the callback function are appended to the **done** queue.

Set **done_callback** to **False** to save memory and processing time if the results are not needed.

If **done_callback** is a **callable** then for every result done_callback will be called.
Please note that done_callback needs to be thread safe!

``submit_first(fn, *args, **kwargs)``
*************************************

Submit a single job to the pool. **fn** is the function to call and ***args** and ****kwargs** the arguments.
The job will be added to the **beginning** of the job queue.

The return value is an id which is the same as the first entry in the result if result_id is set.

``submit_done_first(fn, done_callback, *args, **kwargs)``
*********************************************************

The same as **submit_first** but with an individual done callback function.

``submit_later(delay, fn, *args, **kwargs)``
********************************************

The same as **submit_first** but with a delay in seconds.

``submit_done_later(delay, fn, *args, **kwargs)``
*************************************************

The same as **submit_done_first** but with a delay in seconds.

``submit_at(time, interval, fn, *args, **kwargs)``
**************************************************

The same as **submit_first** but the job is scheduled at a specific time. If **interval** > 0 then the job is scheduled with this interval.

 **time** is start time as float value (like time.time() value) or struct_time.

 **interval** is interval in seconds as float value.

``submit_done_at(time, interval, fn, *args, **kwargs)``
*******************************************************

The same as **submit_at** but with a done callback function.

``delayed``
***********

A property which returns the queue for delayed jobs. The return type is a deque.

``schedule(interval, fn, *args, **kwargs))``
********************************************

Schedule a job which is called with the given interval in seconds. The return value is a TimerObj object. The member timer_id contains the current timer object. If the timer needs to be cancelled it has to be supplied to the cancel function.

``schedule_done(interval, fn, done_callback, *args, **kwargs))``
****************************************************************

Schedule a job which is called with the given interval in seconds.

``scheduled``
*************

A property which returns the queue for scheduled jobs. The return type is a deque.

``as_completed(wait=None)``
***************************

Return an iterator, whose values, when waited for, are the worker results or exceptions in case of failed execution of the worker.

 **wait** if None then wait until all jobs are done. If False then return all finished and failed jobs since last call. If the value is an integer or a float and greater than 0 then as_completed will wait for the specified time.

``map(fn, itr, done_callback=True)``
************************************

Submit a list of jobs, contained in **itr**, to the pool.

**fn** can be a function to call or a generator function.

If **done_callback** is **True** then the results of the callback function are appended to the **done** queue.

Set **done_callback** to **False** to save memory and processing time if the results are not needed.

If **done_callback** is a **callable** then for every result done_callback will be called.
Please note that done_callback needs to be thread safe!

``shutdown(timeout=None, soon=False)``
**************************************

Shutdown the thread pool. If **timeout** is None wait endless else wait up to **timeout** seconds. If **soon** is True then all pending jobs are skipped.

``join(timeout=None)``
**********************

Wait for all client threads to finish. A timeout in seconds can be specified. The function returns False if a timeout was specified and the child threads are still busy. In case of a successful shutdown True is returned.

``cancel(jobid=None, timer=None)``
**********************************

Cancel a single job, all jobs and/or delayed and scheduled jobs.
If **jobid** is None all jobs, but the delayed and scheduled, are cancelled. After all jobs were cancelled True is returned.

If **jobid** is False the job queue is not changed. True is returned.

If **jobid** is a valid job id the specified job are cancelled. If specified job was found and cancelled True is returned, else False is returned.

If **timer** is True all delayed and all scheduled jobs are cancelled.

``clear()``
***********

Clear the queues for the pending, done and failed jobs. Also clear the internal shutdown flag. After resetting the internal queues and flags the thread pool can be reused.

``alive``
*********

A property which returns the number of alive child threads.

``busy``
********

A property which returns the number of busy child threads.

``pending``
***********

A property which returns the number of pending jobs. Also the jobs being currently processed are counted.

``jobs``
********

A property which returns the job queue. The queue of pending jobs waiting to be processed.

``done``
********

A property which returns the queue for results of successfully processed jobs. The queue is a deque object.

``done_cnt``
************

A property which returns a semaphore for the done queue. It can be used to waiting for results without the need for polling.

``failed``
**********

A property which returns the queue for exceptions of failed jobs. The queue is a deque object.

``failed_cnt``
**************

A property which returns a semaphore for the failed queue. It can be used to waiting for results without the need for polling.

Shutdown(now=True):
"""""""""""""""""""

Global shutdown method for all fastthreadpool instances. If **now** is True then all pending jobs are dropped.

Semaphore(value=1)
""""""""""""""""""

This is a fast version of the standard Semaphore implemented in Python. It is more than **20 times faster**.

Semaphore also supports the context management protocol.

``value``
*********

This is a property to get the counter value.

``acquire(blocking=True)``
**************************

Acquire the semaphore.

When invoked without arguments: if the internal counter is larger than zero on entry, decrement it by one and return immediately. If it is zero on entry, block, waiting until some other thread has called release() to make it larger than zero. This is done with proper interlocking so that if multiple acquire() calls are blocked, release() will wake exactly one of them up. The implementation may pick one at random, so the order in which blocked threads are awakened should not be relied on. Returns true (or blocks indefinitely).

When invoked with blocking set to false, do not block. If a call without an argument would block, return false immediately; otherwise, do the same thing as when called without arguments, and return true.

``release()``
*************

Release a semaphore, incrementing the internal counter by one. When it was zero on entry and another thread is waiting for it to become larger than zero again, wake up that thread.

**Examples**
==============

::

 pool = fastthreadpool.Pool()
 pool.map(worker, iterable)
 pool.shutdown()

Results with successful execution were saved in the **done** queue, with failed execution in the **failed** queue.

::

 pool = fastthreadpool.Pool()
 pool.map(worker, iterable, done_cb)
 pool.shutdown()

For every successful execution of the worker the done_cb callback function is called. Results with failed execution in the **failed** queue.

::

 pool = fastthreadpool.Pool(result_id = True)
 job_id1 = pool.submit(worker, foo1)
 pool.shutdown()

Results with successful execution were saved in the **done** queue, with failed execution in the **failed** queue. Each entry in the queues is a tuple with the job_id as the first argument and the result as the second argument.

::

 pool = fastthreadpool.Pool(result_id = True)
 for i in range(100):
     jobid = pool.submit(worker, foo1, i)
 pool.submit_first(worker, foo2)
 pool.cancel(jobid)
 pool.submit_later(0.1, delayed_worker, foo3)
 pool.schedule(1.0, scheduled_worker, foo4)
 time.sleep(1.0)
 pool.cancel(None, True)
 pool.shutdown()

This is a more complex example which shows some of the features of fastthreadpool. First 100 jobs with foo1 and a counter are submitted. Then a job is submitted to the beginning of the job queue. Then the job with foo1 and i=99 is cancelled. Then a job is scheduled for a one time execution in 0.1 seconds. Finally a job is scheduled for repeated execution in a 1 second interval.

Next example shows a use case of an initialization callback function::

 def worker(compressed_data):
     return current_thread().Z.decompress(compressed_data)

 def cbInit(ctx):
     ctx.Z = zstd.ZstdDecompressor()

 pool = fastthreadpool.Pool(init_callback = cbInit)
 for data in iterable:
     pool.submit(worker, data)

Next example shows a simple echo server. The echo server is extremely fast is the buffer size is big enough.
Results have shown on a Ryzen 7 and Linux that this simple server can handle more than 400000 messages / second::

 def pool_echo_server(address, threads, size):
     sock = socket(AF_INET, SOCK_STREAM)
     sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
     sock.bind(address)
     sock.listen(threads)
     with sock:
         while True:
             client, addr = sock.accept()
             pool.submit(pool_echo_client, client, size)

 def pool_echo_client(client, size):
     client.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
     b = bytearray(size)
     bl = [ b ]
     with client:
         try:
             while True:
                 client.recvmsg_into(bl)
                 client.sendall(b)
         except:
             pass

 pool = fastthreadpool.Pool(8)
 pool.submit(pool_echo_server, addr, 8, 4096)
 pool.join()


**Benchmarks**
==============

Example ``ex_semaphore.py`` results on a Celeron N3160 are:

::

 1.8018 seconds for threading.Semaphore
 0.083 seconds for fasthreadpool.Semaphore

fastthreadpool.Semaphore is **21.7** x faster.


Example ``ex_simple_sum.py`` results on a Celeron N3160 are:

::

 0.019 seconds for simple for loop.
 0.037 seconds for simple for loop. Result is saved in class variable.
 0.048 seconds for fastthreadpool.map. Results are save in done queue.
 0.494 seconds for fastthreadpool.submit. Results are save in done queue.
 0.111 seconds for multiprocessing.pool.ThreadPool.map_async.
 21.280 seconds for multiprocessing.pool.ThreadPool.apply_async.

fastthreadpool.map is **2,3** x faster than multiprocessing.pool.ThreadPool.map_async.
fastthreadpool.submit is **43** x faster than multiprocessing.pool.ThreadPool.apply_async.
