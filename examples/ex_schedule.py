
import time
import fastthreadpool

pool = fastthreadpool.Pool()

def Hello(text):
    print(text)
    return "World"

def Done(result):
    print("Done", result)

pool.schedule(1.0, Hello, "Hallo1s")
#pool.schedule_done(2,0, Hello, Done, "Hallo2")
print("SLEEP")
try:
    time.sleep(7)
except:
    pass
print("EXIT")
pool.cancel(None, True)
pool.shutdown()
