import asyncio
from time import monotonic
import datetime
from contextlib import suppress

from loguru import logger
from loadtext import loadtext

from deeplx_pool.batch_deeplx_tr import batch_deeplx_tr, DEQ
from ycecream import y

# turn ycecream off
# y.configure(enabled=False)
# y.configure(output=logger.trace, enabled=False)
# y.configure(output=logger.debug, enabled=1)
# y.configure(return_none=True, enabled=1)

y.configure(o=logger.trace, rn=1)

logger.debug(f"proxies: {len(DEQ)=}")

y(DEQ)
y(DEQ, o=logger.info)

texts = loadtext(r'tests\test.txt', splitlines=1)

# texts = 5 * texts
# texts = 10 * texts

# texts = [f"{idx}__ {elm}" for idx, elm in enumerate(texts)]

then = monotonic()

# _ = asyncio.run(batch_tr(['test 123', 'test abc '] * 100, n_workers=40))
# _ = asyncio.run(batch_tr(['test 123', 'test abc '] * 100, n_workers=len(DEQ)))
# _ = asyncio.run(batch_tr(texts, n_workers=len(DEQ) // 4))

n_workers = 2  # 29 paras 16s
n_workers = 8  # 29 paras 5.6s
n_workers = 16  # 29 paras 4.7s
n_workers = 32  # 29 paras 1.8s 4.0s
n_workers = 10  # 29 paras 3.0s 3.0s
n_workers = 8  # 29 paras 3.0s 4.2s
n_workers = 15  # 29 paras  2.3s
n_workers = 29  # 29 paras  2.0s

n_workers = 50  # 29 paras  3.5s 1.8s
n_workers = 60  # 29 paras  3.5s 1.7s
n_workers = 58  # 29 paras  2.0s 2.0s

n_workers = 58  # 2 x 29 paras  2.0s
n_workers = 58  # 3 x 29 paras  10.4s 17s

# ### n_workers = min(len(DEQ), len(texts))
# len(texts) // len(DEQ) * average req time
# 29 paras  2.3s
# 2x29 paras  4.2s
# 3x29 paras  3.9s
# 5x29 paras  7.1s, len(DEQ)=29 11s
# 10x29 paras  len(DEQ)=29 11s 94.4s
# 50x29 paras 50x29 // len(DEQ) = 33, ?

n_workers = min(len(DEQ), len(texts) // 2)

# n_workers = len(DEQ)  # 29 paras  3.0s
# n_workers = 2 * len(DEQ)  # 29 paras  3.0s

# n_workers = len(DEQ)  # 29 paras  3.0s
# n_workers = len(DEQ) // 2 # 29 paras  4.2s  2.8s

# n_workers > len(texts) probably makes no sense

n_workers = -1  # n_workers = len(texts) // 2
n_workers = 2
n_workers = 1
n_workers = 50
n_workers = 0  # n_workers = len(texts)
n_workers = 19
n_workers = 9

_ = asyncio.run(batch_deeplx_tr(texts, n_workers=n_workers))

# print('[int(isinstance(elm, Exception)) for elm in _])', [int(isinstance(elm, Exception)) for elm in _])

print('\n\n'.join( f"{seqno}: {text}" for seqno, text in sorted(_, key=lambda x: x[0])))

print(f"{n_workers=} {len(DEQ)=}, {len(_)=}, {len(texts)=}, {monotonic() - then: .1f}s")
