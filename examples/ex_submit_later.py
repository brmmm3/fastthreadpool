
import time
import fastthreadpool

pool = fastthreadpool.Pool()


def Hello(text):
    print(text)
    return "World"


def Done(result):
    print("Done", result)


pool.submit_later(1.0, Hello, "Hallo1s")
pool.submit_later(1.1, Hello, "Hallo1.1s")
pool.submit_done_later(1.0, Hello, Done, "Hallo1s")
pool.submit_later(1.0, Hello, "Hallo1s")
pool.submit_later(2.0, Hello, "Hallo2s")
pool.submit_later(5.0, Hello, "Hallo3s")
print("SLEEP")
try:
    time.sleep(7)
except:
    pass
print("EXIT")
pool.cancel(None, True)
pool.shutdown()
