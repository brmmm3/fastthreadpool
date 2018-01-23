An efficient and lightweight thread pool
========================================

Existing implementations of thread pools have a relatively high overhead in certain
situations. Especially apply_async in multiprocessing.pool.ThreadPool and
concurrent.futures.ThreadPoolExecutor at all (see benchmarks).
In case of ThreadPoolExecutor don't use the **wait**. It is *extremely* slow!
If you've only a small number of jobs and the jobs have a relatively long processing
time, then these overheads don't count. But in case of high number of jobs with
short processing time the overhead of the above implementations will noticably
slow down the processing speed.
The fastthreadpool module solves this issue, because it has a very small overhead in
all situations.

**API**
====

**Pool(max_workers = None, thread_name_prefix = "", done_callback = None, failed_callback = None)**

Creating a class instance accepts the above optional arguments. The argument's names are self
explanatory. Worker threads are created on demand as soon as jobs are submitted to the pool.
The **Pool** object contains 3 deque objects **jobs** (pending jobs), **done** (results of successfull
jobs) and **failed** (exceptions of failed jobs).

**submit(fn, *args, **kwargs):**

Submit a single job to the pool. **fn** is the (generator) function to call and *args and **kwargs the arguments.

**submit_done(fn, done_callback, *args, **kwargs):**

The same as **submit** but with an individual done callback function.

**map(fn, itr, done_append = True, shutdown_timeout = None):**

Submit a list of jobs, contained in **itr**, to the pool.
**fn** can be a function to call or a generator function.
If **done_append** is True then the results of the callback function are appended to the **done** queue.
Set **done_append** to False to save memory and processing time if the results are not needed.
If **shutdown_timeout** is not None wait up to **shutdown_timeout** seconds.

**shutdown(timeout = None):**

Shutdown the thread pool. If **timeout** is None wait endless else wait up to **timeout** seconds.

**cancel():**

Cancel all remaining jobs. For joining all worker threads call **shutdown** after **cancel**.

**Usage**
=====

See benchmark.py.

