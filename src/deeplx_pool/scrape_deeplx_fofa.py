"""
Fetch deeplx url from fofa.

cf scrape_deeplx_shodan.py

Use diskcache to throttle and store deeplx-sites

httpx
pyquery
diskcache
loguru
rich

invoke
"""

# pylint: disable=invalid-name, broad-except, line-too-long, too-many-statements
import asyncio
import base64
import re
from datetime import timedelta
from pathlib import Path
from random import choice
from time import time
from typing import List, Union

import diskcache
import httpx
from httpx import Timeout
from loguru import logger
from pyquery import PyQuery as pq
from rich.console import Console

from deeplx_pool.check_deeplx import check_deeplx_async

cache = diskcache.Cache(Path.home() / ".diskcache" / "deeplx-sites")

# no need, just use default=None in cache.get
# create "sentinel" if not exist, for throttling scrape_deeplx_shodan/fofa
# if "sentinel" not in list(cache): cache.set("sentinel", None)

SENTINEL_EXPIRE = 600  # 10 minutes

# sentinel will be None after sentinel_expire
# only scrape if cache.get("sentinel") is not None

# from duration_human import duration_human

# url = httpx.get("""https://www.shodan.io/search?query=DeepL+Translate+Api""", timeout=120)
# url = "https://www.shodan.io/search"

# docker https://huggingface.co/spaces/vinhson/deeplx
# FROM ghcr.io/xiaoxuan6/deeplx:latest
# """body='{"code":200,"msg":"welcome to deeplx"}'"""

query_def1 = '''"deepl translate api" && country="CN"'''
query_def2 = '''body='{"code":200,"message":"DeepL Free API, Developed by sjlleo and missuo. Go to /translate with POST. http://github.com/OwO-Network/DeepLX"}' && country="CN"'''
query_def3 = '''"welcome to deeplx" && country="CN"'''
query_def = choice([query_def1, query_def2, query_def3])

DURATION_HUMAN_SPEC = (
    (1.0e-6, 1e9, 1e3, "ns"),
    (1.0e-3, 1e6, 1e3, "us"),
    (1.0, 1e3, 1e3, "ms"),
    (60.0, 1e0, 60.0, "s"),
)
console = Console()


def duration_human(value: float) -> str:
    """
    Return a beautiful representation of the duration.

    It dynamically calculates the best unit to use.

    Returns
    -------
        str: the duration representation.

    """
    try:
        value = round(value, 2)
    except Exception:
        return str(value)

    for (
        top,
        mult,
        size,
        unit,
    ) in DURATION_HUMAN_SPEC:
        if value < top:
            result = round(value * mult, ndigits=2)
            if result < size:
                return f"{result}{unit}"
    try:
        txt = str(timedelta(seconds=float(f"{value:.1f}")))
        pos = txt.find(".")
        if pos == -1:
            return txt
        return txt[: pos + 2]
    except OverflowError:
        return "quasi-infinity \n(Python int too large to convert to C int)"


def scrape_deeplx_fofa(
    query: str = "",
    timeout: Union[float, Timeout] = Timeout(30),
    throttle: bool = True,
) -> List[str]:
    """
    Fetch deeplx url from fofa.

    Args:
    ----
    query: phrase to search in shoda, default '''"deepl translate api" && country="CN"'''
    timeout: timeout for httpx
    throttle: if True, check cache.get("sentinel", default True

    Returns:
    -------
    list of deeplx sites or None (when run too soon [within 10 minutes])

    """
    if not query:
        query = choice([query_def1, query_def2, query_def3])

    # check sentinel-fofa in cache
    value, expire_time = cache.get(  # type: ignore
        "sentinel-fofa",
        default=None,
        expire_time=True,
    )

    if throttle and (value is not None):  # throttle is set, not expire yet
        if expire_time is not None:
            _ = duration_human(expire_time - time())  # type: ignore
            console.print(
                f"{__file__}: too soon, try again in {_}.",
                style="yellow",
            )
        else:
            console.print(
                f"{__file__}: too soon, try again later.",
                style="yellow",
            )
        return []

    url = f"https://en.fofa.info/result?qbase64={base64.b64encode(query.encode()).decode()}"

    logger.trace(f"{url=}, {query=}")
    logger.debug(f"{url=}, {query=}")
    try:
        res = httpx.get(
            url,
            timeout=timeout,
            verify=False,
        )
        res.raise_for_status()
        text = res.text
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {e.request.url!r}: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error response {e.response.status_code} while requesting {e.request.url!r}: {e.response.text}")
    except Exception as exc:
        logger.error(exc)
        raise
    logger.trace(f"{text[:100]=}")

    url_list = [elm.attrib["href"] for elm in pq(res.text)(".hsxa-host > a")]

    # re-set/set sentinel with SENTINEL_EXPIRE time
    cache.set(
        "sentinel-fofa",
        True,
        expire=SENTINEL_EXPIRE,
    )

    return url_list


async def main():
    """Bootsrap."""
    console.print("diggin...", style="yellow")
    then = time()

    # try 3 times with increased timeout
    for _ in range(3):
        console.print(
            "fetching info from fofa",
            style="yellow",
        )
        if _ > 0:
            logger.info(f"Retry: {_}")
        try:
            timeout = Timeout(30 * 1.2**_)
            url_list = scrape_deeplx_fofa(timeout=timeout)
            break
        except httpx.ReadTimeout:
            continue
        except Exception as exc:
            logger.error(exc)
            continue
    else:
        logger.warning(
            "Tried 3 tiems, "
            "see previous error messages, no network? "
            "Make sure you can visit https://en.fofa.info."
        )
        raise Exception("Make sure you can visit https://en.fofa.info.")

    # exit if scrape_deeplx_fofa returns None
    # if url_list is None: return None

    url_list_hist = cache.get("deeplx-sites", [])

    console.print("Saved urls: ", url_list_hist)

    console.print("Fetched urls: ", url_list)
    # console.print('\n'.join(url_list))
    console.print(
        f"Time used: {duration_human(time() - then)}",
        style="green",
    )

    # extract urls. combine, deduplicate, convert back to list
    _ = list(dict(url_list_hist))  # type: ignore
    _ = set(_ + url_list)
    url_list = list(_)

    # append extra sites to check
    extra_urls = [
        # "https://translates.me/v2",
        "https://api.deeplx.org",
        "http://142.171.18.103",
    ]
    extra_urls = ["https://api.deeplx.org"]

    # quick scrape deeplx.wangwangit.com
    for _ in range(3):
        try:
            res = httpx.get(
                "https://deepl.wangwangit.com/",
                timeout=20,
            )
            lst = re.findall(
                r"https?://[\d.]+(?::\d+)?",
                res.text,
            )
            logger.trace(f"wangwangit: {lst}")
            extra_urls.extend(lst)
            break
        except (
            httpx.ConnectError,
            httpx.ConnectTimeout,
        ):
            continue
        except Exception as exc:
            logger.error(exc)
            break
    else:
        console.print(
            "Tried 3 times, deepl.wangwangit.com probably down or blocked this ip."
        )

    console.print(f"{extra_urls[:3]=}")

    for elm in extra_urls:
        if elm not in url_list:
            url_list.append(elm)

    console.print("Combined urls: ", url_list)

    then = time()
    urls_checked = await asyncio.gather(
        *map(check_deeplx_async, url_list),
        return_exceptions=True,
    )

    # urls_checked = [*map(check_url, url_list)]

    # save valid urls to cache
    urls_valid = [_ for _ in urls_checked if isinstance(_[1], float)]  # type: ignore
    # sorted
    urls_valid = sorted(urls_valid, key=lambda x: x[1])  # type: ignore

    cache.set("deeplx-sites", urls_valid)

    console.print("Checked urls:", urls_checked)
    console.print(
        f"Time elapsed: {duration_human(time() - then)}",
        style="green",
    )

    total = len(urls_valid)
    console.print(
        "Valid urls:",
        urls_valid,
        f"{total=}",
    )


if __name__ == "__main__":
    asyncio.run(main())

    _ = """
    try:
        # main()
        asyncio.run(main())
    except Exception as exc_:
        logger.error(exc_)
        raise SystemExit(1) from exc_
    # """
