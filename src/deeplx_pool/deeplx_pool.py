"""
Collect deeplx-urls.

based on scrape_deeplx_shodan.py
"""
# pylint: disable=too-many-statements, too-many-branches, broad-exception-caught, too-many-locals, line-too-long

import asyncio
import itertools
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import re
from pathlib import Path
from time import time

import diskcache
import httpx
from httpx import Timeout
from loguru import logger
from rich.console import Console

from deeplx_pool.check_deeplx import check_deeplx_async
from deeplx_pool.fetch_urls_fofa_hack import fetch_urls_fofa_hack
from deeplx_pool.scrape_deeplx_fofa import scrape_deeplx_fofa
from deeplx_pool.scrape_deeplx_shodan import scrape_deeplx_shodan

DURATION_HUMAN_SPEC = (
    (1.0e-6, 1e9, 1e3, "ns"),
    (1.0e-3, 1e6, 1e3, "us"),
    (1.0, 1e3, 1e3, "ms"),
    (60.0, 1e0, 60.0, "s"),
)
console = Console()

cache = diskcache.Cache(Path.home() / ".diskcache" / "deeplx-sites")


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


# async def main():
def main():
    """Bootstrap."""
    url_list_hist = cache.get("deeplx-sites", [])
    console.print("Saved urls: ", url_list_hist, len(url_list_hist))  # type: ignore

    # ########## shodan ##########
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
            timeout = Timeout(60 * 1.5 ** _)
            url_list_shodan = scrape_deeplx_shodan(timeout=timeout)
            break
        except httpx.ReadTimeout:
            continue
        except Exception as exc:
            logger.error(exc)
            continue
    else:
        url = "https://www.shodan.io/search"
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

    url_list_fofa = []
    # ########## fofa no more ##########
    _ = """
    console.print("diggin fofa...", style="yellow")
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
            url_list_fofa = scrape_deeplx_fofa(timeout=timeout)
            break
        except httpx.ReadTimeout:
            continue
        except Exception as exc:
            logger.error(exc)
            continue
    else:
        url = "https://en.fofa.info"
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
    # """

    # ########## fofa_hack api ##########
    then = time()
    url_list_fofa_hack = []
    try:
        query_def1 = '''"deepl translate api" && country="CN"'''
        query_def2 = '''body='{"code":200,"message":"DeepL Free API, Developed by sjlleo and missuo. Go to /translate with POST. http://github.com/OwO-Network/DeepLX"}' && country="CN"'''
        query_def3 = '''"welcome to deeplx" && country="CN"'''
        query_def4 = '''"Welcome to deeplx-pro"'''
        # query_def = choice([query_def1, query_def2, query_def3])
        queries = [query_def1, query_def2, query_def3, query_def4]

        with ThreadPoolExecutor() as pool:
            urls = [*pool.map(fetch_urls_fofa_hack, queries)]

        url_list_fofa_hack = [*itertools.chain(*urls)]

    except Exception as exc:
        logger.error(exc)
    console.print("Fetched fofa_hack urls: ", len(url_list_fofa_hack))
    console.print(
        f"Time used: {duration_human(time() - then)}",
        style="green",
    )

    # ########## misc extra ##########
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

    # done in proc_static.py
    _ = r"""
    filename = "linuxdo216930.txt"
    try:
        filecont = Path(filename).read_text(encoding="utf8").strip()
    except Exception as exc:
        logger.error(exc)
        filecont = ""
    urls_file = re.split(r"[\s,;；，]+", filecont)
    urls_file = [elm.strip() for elm in urls_file if elm.strip()]
    logger.info(f"{len(urls_file)=}")
    extra_urls.extend(urls_file)
    # """

    _ = """
    for elm in extra_urls:
        if elm not in url_list:
            url_list.append(elm)
    # """

    # extract urls, combine, deduplicate, convert back to list
    _ = list(dict(url_list_hist))  # type: ignore
    _ = set(_ + url_list_shodan + url_list_fofa + url_list_fofa_hack + extra_urls)
    url_list = list(_)

    console.print("Combined urls: ", url_list)
    console.print(f"\t # of combined urls: {len(url_list)}")

    async def gather():
        return await asyncio.gather(
            *map(check_deeplx_async, url_list),
            return_exceptions=True,
        )

    then = time()
    # urls_checked = await asyncio.gather(
    urls_checked = asyncio.run(gather())

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
    # asyncio.run(main())
    main()

    _ = """
    try:
        # main()
        asyncio.run(main())
    except Exception as exc_:
        logger.error(exc_)
        raise SystemExit(1) from exc_
    # """
