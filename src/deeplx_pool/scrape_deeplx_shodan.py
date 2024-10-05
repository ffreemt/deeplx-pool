"""
Fetch deepkx url from shodan.

Use diskcache to throttle and store deeplx-sites

httpx
pyquery
diskcache
loguru
rich

invoke
"""

# pylint: disable=invalid-name, broad-except, line-too-long, too-many-statements, too-many-branches
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from random import choices
from time import time
from typing import List, Union

import diskcache
import httpx
from httpx import Timeout
from loguru import logger
from pyquery import PyQuery as pq
from rich.console import Console

from deeplx_pool.check_deeplx import check_deeplx_async
from deeplx_pool.scrape_deeplx_fofa import scrape_deeplx_fofa

cache = diskcache.Cache(Path.home() / ".diskcache" / "deeplx-sites")

# no need, just use default=None in cache.get
# create "sentinel" if not exist, for throttling scrape_deeplx_shodan
# if "sentinel" not in list(cache): cache.set("sentinel", None)

SENTINEL_EXPIRE = 600  # 10 minutes

# sentinel will be None after sentinel_expire
# only scrape if cache.get("sentinel") is not None

# from duration_human import duration_human

# url = res1 = httpx.get("""https://www.shodan.io/search?query=DeepL+Translate+Api""", timeout=120)
url = "https://www.shodan.io/search"

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


def scrape_deeplx_shodan(
    query: str = "",
    timeout: Union[float, Timeout] = Timeout(30),
    throttle: bool = True,
) -> List[str]:
    """
    Fetch deeplx url from shodan.

    Args:
    ----
    query: phrase to search in shoda, default "deepl api"
    timeout: timeout for httpx
    throttle: if True, check cache.get("sentinel", default True

    Returns:
    -------
    list of deeplx sites or None (when run too soon [within 10 minutes])

    """
    if not query:
        query = choices(["deepl api", "welcome to deeplx"])[0]
    logger.debug(f"{query=}")
    # check sentinel in cache
    value, expire_time = cache.get(  # type: ignore
        "sentinel",
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

    logger.trace(f"{url=}, {query=}")
    try:
        res = httpx.get(
            f"{url}?query={query}",
            timeout=timeout,
            verify=False,
        )
        res.raise_for_status()
        text = res.text
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {e.request.url!r}: {e}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Error response {e.response.status_code} while requesting {e.request.url!r}: {e.response.text}"
        )
        return []
    except Exception as e:
        logger.error(e)
        raise
    logger.trace(f"{text[:100]=}")

    # result = doc('a').filter(lambda i, this: pq(this).find('dd'))

    # pick .heading > a that has "target" attrib
    # pq(text)('.heading > a')[0].attrib
    # {'href': '/host/178.170.41.47', 'class': 'title text-dark'}
    # pq(text)('.heading > a')[1].attrib
    # {'href': 'http://178.170.41.47:8181', 'target':
    # '_blank', 'rel': 'noopener noreferrer nofollow', 'class': 'text-danger'}

    nodes = pq(text)(".heading > a").filter(lambda idx, elm: "target" in elm.attrib)

    # extract href
    url_list = [elm.attrib["href"] for elm in nodes]

    _ = """
    try:
        url_list = [elm.attrib["href"] for elm in pq(text)(".hsxa-host > a")]
    except Exception as exc:
        logger.error(exc)
        raise
    # """

    # re-set/set sentinel with SENTINEL_EXPIRE time
    cache.set(
        "sentinel",
        True,
        expire=SENTINEL_EXPIRE,
    )

    return url_list


async def main():
    """Bootsrap."""
    url_list_hist = cache.get("deeplx-sites", [])
    console.print("Saved urls: ", url_list_hist)

    console.print("diggin shodan...", style="yellow")
    then = time()
    # try 3 times with increased timeout
    url_list_shodan = []
    for _ in range(3):
        console.print(
            "fetching info from shodan",
            style="yellow",
        )
        if _ > 0:
            logger.info(f"Retry: {_}")
        try:
            timeout = Timeout(30 * 1.2**_)
            url_list_shodan = scrape_deeplx_shodan(timeout=timeout)
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
            f"Make sure you can visit {url}."
        )
        # raise Exception(f"Make sure you can visit {url}.")

    console.print("Fetched shodan urls: ", url_list_shodan)
    console.print(
        f"Time used: {duration_human(time() - then)}",
        style="green",
    )
    # ---

    console.print("diggin fofa...", style="yellow")
    then = time()
    # try 3 times with increased timeout
    url_list_fofa = []
    for _ in range(3):
        console.print(
            "fetching info from fofa",
            style="yellow",
        )
        if _ > 0:
            logger.info(f"Retry: {_}")
        try:
            timeout = Timeout(30 * 1.2**_)
            url_list_fofa = scrape_deeplx_fofa(timeout=timeout)
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
            f"Make sure you can visit {url}."
        )
        # raise Exception(f"Make sure you can visit {url}.")
        logger.warning(f"Make sure you can visit {url}.")

    console.print("Fetched fofa urls: ", url_list_fofa)
    console.print(
        f"Time used: {duration_human(time() - then)}",
        style="green",
    )
    # ---

    # extract urls. combine, deduplicate, convert back to list
    _ = list(dict(url_list_hist))  # type: ignore
    _ = set(_ + url_list_shodan + url_list_fofa)
    url_list = list(_)

    # append extra sites to check

    # quick scrape deeplx.wangwangit.com
    extra_urls = []

    _ = r""" deeplx.wangwangit.com, no longer valid
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
    # """

    _ = [
        # "https://translates.me/v2",
        # "https://api.deeplx.org/linxdo_key",  # from https://connect.linux.do/
        "https://deeplx.niubipro.com",
        "https://freedeeplxapi1.ddl.us.kg",
        "https://ihabis-deeplx-test2-no-token.hf.space",
        "https://wuran-deeplx.hf.space",
        "https://uu0103-deeplx.hf.space",
        "https://xcq-1-deeplx.hf.space",
        "https://mikeee-deeplx.hf.space",
        "https://deeplx.dattw.eu.org",
        # deeplx-local at hf
        "https://mikeee-deeplx-local.hf.space",
        "https://bestmaple-deeplx-local.hf.space",
    ]
    # extra_urls = ["https://api.deeplx.org"]

    extra_urls.extend(_)

    console.print(f"{extra_urls=}")

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
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    return total


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
