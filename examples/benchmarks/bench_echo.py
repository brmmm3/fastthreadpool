
import time
import argparse
import subprocess

import echoclient


class Args:
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--disconnect', default=False, action='store_true',
                        help='disconnect after every message')
    args = parser.parse_args()
    clientArgs = Args()
    clientArgs.mpr = 1
    clientArgs.num = 20000
    clientArgs.times = 1
    clientArgs.workers = 5
    clientArgs.addr = '127.0.0.1:25000'
    clientArgs.disconnect = args.disconnect
    results = []
    for srvArgs in ("", "--streams", "--proto",
                    "--uvloop", "--uvloop --streams", "--uvloop --proto",
                    "--pool --bufsize 4096", "--pool --bufsize 8192",
                    "--pool --bufsize 16384", "--pool --bufsize 32768",
                    "--pool --bufsize 65536", "--pool --bufsize 131072",
                    "--pool --bufsize 262144"):
        prc = subprocess.Popen(f"python3.7 echoserver.py {srvArgs}".split())
        if "--uvloop" in srvArgs:
            title = "uvloop/" + srvArgs.split(" --")[1]
            bufSize = ""
        elif "--pool" in srvArgs:
            title = "threads"
            bufSize = srvArgs.split("--bufsize ")[1]
        else:
            title = "asyncio/" + srvArgs.lstrip("-")
            bufSize = ""
        print("-------")
        time.sleep(0.5)
        try:
            for msgSize in (1000, 4096, 16384, 65536):
                clientArgs.msize = msgSize
                if msgSize == 1000:
                    size = "1000 bytes"
                elif msgSize == 4096:
                    size = "4kB"
                elif msgSize == 16384:
                    size = "16kB"
                else:
                    size = "64kB"
                msgSpeed, mbSpeed = echoclient.main(clientArgs)
                results.append((title, bufSize, size, msgSpeed, mbSpeed))
                print()
        except KeyboardInterrupt:
            raise
        except:
            import traceback
            traceback.print_exc()
        finally:
            prc.terminate()
    print("\n".join([" | ".join(result) for result in results]))
