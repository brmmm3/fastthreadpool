
import time
import fastthreadpool

if __name__ == "__main__":
    startTime = time.time()

    pool = fastthreadpool.Pool()

    def Hello(text):
        print(time.time() - startTime, text)
        return "World " + text

    def Done(result):
        print(time.time() - startTime, "Done", result)

    tmr1s = pool.schedule(1.0, Hello, "Hallo 1s")
    print("1s timer", tmr1s)
    tmr15s = pool.schedule_done(1.5, Hello, Done, "Hallo 1.5s")
    print("1.5s timer", tmr15s)
    pool.submit_at(startTime + 1.8, 0.0, Hello, "Submit At")
    pool.submit_at(startTime + 3.8, 0.0, Hello, "Submit At 2")
    pool.submit_at(startTime + 1.9, 0.8, Hello, "Submit At Interval")
    print("SLEEP")
    try:
        time.sleep(5)
    except:
        pass
    print("CANCEL 1.5s timer", tmr15s)
    pool.cancel(None, tmr15s)
    print("SLEEP")
    try:
        time.sleep(5)
    except:
        pass
    print("EXIT")
    pool.cancel(None, True)
    pool.shutdown()
