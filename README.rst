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

The API is described `here <doc/API.rst>`_.

Examples
========

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
