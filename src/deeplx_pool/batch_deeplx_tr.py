"""
Translate using deeplx-sites from cache.get("deeplx-sites").

cache = diskcache.Cache(Path.home() / ".diskcache" / "deeplx-sites")

# reverse, prepare for deq[-1] and deq.rotate
deq = deque([url for url, deplay in cache.get("deeplx-sites")[::-1]]
"""
# pylint: disable=too-many-branches, too-many-statements
import asyncio
from collections import deque
from pathlib import Path
from random import randrange
from time import monotonic
from typing import List, Tuple, Union

import diskcache
from loguru import logger
from ycecream import y

from deeplx_pool.deeplx_client_async import deeplx_client_async

cache = diskcache.Cache(Path.home() / ".diskcache" / "deeplx-sites")
_ = cache.get("deeplx-sites") or []  # "or []" takes care of first run
DEQ = deque([url for url, delay in _[::-1]])  # type: ignore


async def cache_incr(item, idx, inc=1):
    """Increase cache.get(item)[idx] += inc."""
    _ = cache.get(item)
    # silently ignore all exceptions
    try:
        # _[idx] = _[idx] + inc
        _[idx] += inc
    except Exception:
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, cache.set, item, _)


async def worker(
    queue, deq, wid=-1, queue_tr=asyncio.Queue()
) -> List[List[Union[str, BaseException]]]:
    """
    Translate text in the queue.

    Args:
    ----
    queue: asyncio.Queue that contains list of texts
    deq: collections.deque to hold deeplx urls
    wid: identifier
    queue_tr: common queue for all workers to store trtext and for stop condition

    url: deeplx site's url from a deque

    """
    # asign a random wid by default
    if wid < 0:
        randrange(1000)
    logger.trace(f"******** {wid=}")
    trtext_list = []

    # while not queue.empty():
    # try n times and break
    n_attempts = queue.qsize()
    n_texts = n_attempts

    logger.trace(f"{n_attempts=} {wid=}")

    _ = """
    for _ in range(n_attempts):
        logger.trace(f"attemp {_ + 1}  {wid=} ")
        if queue.empty():
            logger.trace(f" queue empty, done {wid=} ")
            break

        try:
            seqno_text = queue.get_nowait()
            logger.trace(f"{seqno_text=}")
            if len(seqno_text) == 2:
                seqno, text = seqno_text
            else:
                text = str(seqno_text)
                seqno = -1
        # another worker maybe manages to empty the queue in the mean time
        except asyncio.QueueEmpty as exc:
            logger.warning(f"This should not happen, unless there is a race, {exc=}")
            text = exc
            break
        except Exception as exc:
            logger.warning(f"{exc=}")
            raise

        # process output (text) from queue.get_nowait()
        if not isinstance(text, asyncio.QueueEmpty):
            # fetch an url from deq's end
            # do we need to lock deq properly?
            url = deq[-1]
            deq.rotate()
            logger.trace(f" deq rotated: {deq=}")
            logger.trace(f" {url=}")
            logger.trace(f" {text=}")

            # httpx.HTTPStatusError
            try:
                logger.trace(f" try deeplx_client_async {text=} {wid=}")
                trtext = await deeplx_client_async(text, url=url)
                logger.trace(f" done deeplx_client_async {text=} {wid=}")
            except Exception as exc:
                logger.trace(f"{exc=}, {wid=}")
                # raise
                trtext = exc  # for retry in the subsequent round

                # remove url from DEQ since it does not deliver
                try:
                    # DEQ.remove(url)
                    ...
                except Exception: # maybe another worker already did
                    ...
            finally:
                logger.trace(f" {trtext=}  {wid=} ")
                queue.task_done()
                logger.trace(f"\n\t >>====== que.task_done()  {wid=}")

                # put text back in the queue if Exception
                if isinstance(trtext, Exception):
                    logger.info(f" {seqno=} failed {trtext=}, back to the queue")
                    await queue.put((seqno, text))
                    await cache_incr("workers_fail", wid)
                else:
                    # text not empty but text.strip() empty, try gain
                    if text.strip() and not trtext.strip():
                        logger.info(f" {seqno=} empty trtext, back to the queue")
                        # try again if trtext empty
                        await queue.put((seqno, text))
                        await cache_incr("workers_emp", wid)
                    else:
                        logger.info(f" {seqno=} done ")
                        trtext_list.append((seqno, trtext))
                        await cache_incr("workers_succ", wid)
    else:
        logger.trace(f" max attempts reached {wid=}")
    # """

    then = monotonic()
    while True:
        # test timeout realy exit
        # if monotonic() - then > 1: break

        # break based on len(trtext_list) and time
        # if len(trtext_list) >= n_texts or monotonic() - then > 30 * n_texts:
        if queue_tr.qsize() >= n_texts or monotonic() - then > 30 * n_texts:
            break

        try:
            seqno_text = queue.get_nowait()
            logger.trace(f"{seqno_text=}")

            # there is no need for this 'if', but just to play safe
            if len(seqno_text) == 2:
                seqno, text = seqno_text
            else:
                text = str(seqno_text)
                seqno = -1
        except asyncio.QueueEmpty:
            # logger.info(f"Currently no items in the queue: {exc}")
            await asyncio.sleep(0.1)
            continue  # other worker may fail and put back items to the queue
        except Exception as exc:
            logger.warning(f"{exc=}")
            raise

        # process text, output from queue.get_nowait()
        url = deq[-1]
        deq.rotate()
        logger.trace(f" deq rotated: {deq=}")
        logger.trace(f" {url=}")
        logger.trace(f" {text=}")

        # httpx.HTTPStatusError
        try:
            logger.trace(f" try deeplx_client_async {text=} {wid=}")
            trtext = await deeplx_client_async(text, url=url)
            logger.trace(f" done deeplx_client_async {text=} {wid=}")
        except Exception as exc:
            logger.trace(f"{exc=}, {wid=}")
            # raise
            trtext = exc  # for retry in the subsequent round

            # optinally, remove url from DEQ since it does not deliver
            try:
                # DEQ.remove(url)
                ...
            except Exception:  # maybe another worker already did DEQ.remove(url)
                ...
        finally:
            logger.trace(f" {trtext=}  {wid=} ")
            queue.task_done()
            logger.trace(f"\n\t >>====== que.task_done()  {wid=}")

            # put text back in the queue if Exception
            if isinstance(trtext, Exception):
                logger.trace(f"{wid=} {seqno=} failed {trtext=}, back to the queue")
                await queue.put((seqno, text))
                await cache_incr("workers_fail", wid)
                await asyncio.sleep(0.1)  # give other workers a chance to try
            else:
                # text not empty but text.strip() empty, try gain
                if text.strip() and not trtext.strip():
                    logger.trace(f"{wid=} {seqno=} empty trtext, back to the queue")
                    # try again if trtext empty
                    await queue.put((seqno, text))
                    await cache_incr("workers_emp", wid)
                    await asyncio.sleep(0.1)
                else:
                    logger.info(f"{wid=} {seqno=} done ")
                    trtext_list.append((seqno, trtext))
                    await queue_tr.put((seqno, trtext))
                    await cache_incr("workers_succ", wid)

    logger.trace(f"\n\t {trtext_list=}, {wid=} fini")

    return trtext_list


async def batch_deeplx_tr(texts: List[str], n_workers: int = 4) -> List[Tuple[int, str]]:
    """
    Translate in batch using urls from deq.

    Args:
    ----
        texts: list of text to translate
        n_workers: number of workers

    Returns:
    -------
        list of translated texts

    refer to python's official doc's example and asyncio-Queue-consumer.txt.

    """
    # logger.trace(f"{texts=}")
    # logger.trace(y(texts))

    try:
        n_workers = int(n_workers)
    except Exception:
        n_workers = 4
    if n_workers == 0:
        n_workers = len(texts)
    elif n_workers < 0:
        n_workers = len(texts) // 2

    # cap to len(texts)
    n_workers = min(n_workers, len(texts))

    logger.info(f"{n_workers=}")

    logger.debug(y(n_workers))

    que = asyncio.Queue()
    for idx, text in enumerate(texts):
        await que.put((idx, text))  # attach seq no for retry

    logger.trace(f"{que=}")

    # n_workers = 2
    # n_workers = 20
    # coros = [worker(que, DEQ, _) for _ in range(n_workers)]

    # does not run, must wrap in with asyncio.create_task
    # tasks = [worker(que, DEQ, _) for _ in range(n_workers)]

    # collect stats about workers
    # cache.set('workers_succ')
    # cache.set('workers_fail')
    # cache.set('workers_emp')
    cache.set("workers_succ", [0] * n_workers)
    cache.set("workers_fail", [0] * n_workers)
    cache.set("workers_emp", [0] * n_workers)

    tasks = [asyncio.create_task(worker(que, DEQ, _)) for _ in range(n_workers)]

    # no longer needed since we exit only when len(trtexts) >= len(texts) or timeout
    # await que.join()  # queue.task_done() for each task to properly exit

    logger.trace("\n\t  >>>>>>>> after  await que.join()")

    # give the last task some time, no need since we monitor tretxt_list
    # await asyncio.sleep(.1)

    # Cancel our worker tasks, do we need this?
    # for task in tasks: task.cancel()

    logger.trace("\n\t >>>>>>>> Start await asyncio.gather")

    # consume texts_list in an async way
    # trtext_list = await asyncio.gather(*coros, return_exceptions=True)

    # trtext_list = await asyncio.gather(*tasks, return_exceptions=True)
    trtext_list = await asyncio.gather(*tasks)

    logger.trace("\n\t  >>>>>>>> Done await asyncio.gather")

    # print(trtext_list[:3])

    logger.trace(f"{trtext_list=}")
    # return trtext_list

    # trtext_list can be asyncio.CancelledError in which case

    trtext_list1 = []
    for _ in trtext_list:
        trtext_list1.extend(_)  # type: ignore
    logger.trace(f"{trtext_list1=}")

    succ = cache.get("workers_succ")
    logger.info(f"""success\n\t {succ}, {sum(succ)}""")
    logger.info(f"""failure\n\t {cache.get("workers_fail")}""")
    logger.info(f"""empty\n\t {cache.get("workers_emp")}""")

    return trtext_list1


if __name__ == "__main__":
    _ = asyncio.run(batch_deeplx_tr(["test 123", "test abc "]))
    print(_)
