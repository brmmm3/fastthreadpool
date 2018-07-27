import time
import gc
import lz4.block
import zstandard as zstd
import msgpack
import fastthreadpool
from threading import current_thread

C = zstd.ZstdCompressor(write_content_size=True, write_checksum=True, level=14)
D = zstd.ZstdDecompressor()

cnt = 10000
c2 = 10000
l = list(range(cnt))
d = C.compress(msgpack.packb(l))


class A:
    up = msgpack.unpackb

    @staticmethod
    def worker(w):
        return A.up(current_thread().Z.decompress(w))

    @staticmethod
    def worker0(w):
        return A.up(zstd.ZstdDecompressor().decompress(w))

    @staticmethod
    def worker2(w):
        gc.disable()
        r = A.up(current_thread().Z.decompress(w))
        gc.enable()
        return r


def cbInit(ctx):
    ctx.Z = zstd.ZstdDecompressor()


if __name__ == "__main__":
    p = fastthreadpool.Pool(init_callback=cbInit)
    t1 = time.time()
    for _ in range(c2):
        p.submit_done(A.worker, False, d)
    p.shutdown()
    dt = time.time() - t1
    print(dt, dt / c2)

    p = fastthreadpool.Pool(init_callback=cbInit)
    t1 = time.time()
    gc.disable()
    for _ in range(c2):
        p.submit_done(A.worker, False, d)
    gc.enable()
    p.shutdown()
    dt = time.time() - t1
    print(dt, dt / c2)

    p = fastthreadpool.Pool(init_callback=cbInit)
    t1 = time.time()
    for _ in range(c2):
        p.submit_done(A.worker2, False, d)
    p.shutdown()
    dt = time.time() - t1
    print(dt, dt / c2)

    t1 = time.time()
    for _ in range(c2):
        r = A.worker0(d)
    dt = time.time() - t1
    print(dt, dt / c2)

