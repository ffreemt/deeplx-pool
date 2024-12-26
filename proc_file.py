"""
Check and time urls from a file (default  fofa-results.txt).

Inject urls in a file to diskcache deeplx-sites.
"""
# pylint: disable=broad-exception-caught

import asyncio
from datetime import timedelta
import re
from pathlib import Path
from time import time

import diskcache
from loguru import logger
from rich.console import Console

from deeplx_pool.check_deeplx import check_deeplx_async

cache = diskcache.Cache(Path.home() / ".diskcache" / "deeplx-sites")
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


def proc_file(filename=""):
    """
    Process filename.

    Verify and time reponse time.
    """
    if not filename:
        filename = "linuxdo216930.txt"
        filename = "fofa-results.txt"

    # DeepL Free API, Developed by sjlleo and missuo
    # fofa-results6.txt

    try:
        filecont = (
            Path("linuxdo216930.txt").read_text(encoding="utf8")
            + Path("fofa-results6.txt").read_text(encoding="utf8")
            + Path(filename).read_text(encoding="utf8")
        )
        # filecont = Path("fofa-results6.txt").read_text(encoding="utf8").strip()
    except Exception as exc:
        logger.error(exc)
        filecont = ""

    # urls = re.split(r"[\s,;]+", filecont)
    # urls = [elm.strip().strip("/") for elm in urls if elm.strip()]

    urls = re.findall(r"https?://[\w.:-]+", filecont)

    logger.info(f"{len(urls)=}")

    url_list_hist = cache.get("deeplx-sites", [])
    _ = list(dict(url_list_hist))  # type: ignore
    urls = set(_ + urls)
    urls = list(urls)

    async def gather():
        return await asyncio.gather(
            *map(check_deeplx_async, urls),
            return_exceptions=True,
        )

    then = time()
    # urls_checked = await asyncio.gather(
    urls_checked = asyncio.run(gather())
    console.print("Checked urls:", urls_checked)
    console.print(
        f"Time elapsed: {duration_human(time() - then)}",
        style="green",
    )

    # save valid urls to cache
    urls_valid = [_ for _ in urls_checked if isinstance(_[1], float)]  # type: ignore

    # sorted
    urls_valid = sorted(urls_valid, key=lambda x: x[1])  # type: ignore

    logger.info(f"urls_valid: {len(urls_valid)}")
    if urls_valid:
        cache.set("deeplx-sites", urls_valid)
        console.print(
            urls_valid,
            f"{len(urls_valid)} to diskcache deeplx-sites",
            style="green",
        )
    else:
        console.print(
            urls_valid,
            "Is the net down?",
            style="red bold",
        )


if __name__ == "__main__":
    proc_file()
