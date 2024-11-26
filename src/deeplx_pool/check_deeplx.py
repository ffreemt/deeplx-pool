r"""
Check url for valid deeplx service.

url = 'http://124.70.179.239:8080'
url = 'http://39.107.110.63:8080/'
url = 'http://acone:8080/'
url = 'http://114.215.113.138:4499/'

lst = [(True, 2.46), (True, 1.1), (True, 2.2), (False, 'aaa')]

for check, latency_or_error
filter and sort: sorted(filter(lambda x: x[0], lst), key=lambda x: x[1])

filter (<=5s) and sort: sorted(filter(lambda x: x[0] and x[1] <= 5, lst), key=lambda x: x[1])

filter failed url
    filter(lambda x: not x[0] and x[1] <= 5, lst)

lst1 = [('url1', 2.46), ('url2', 1.1), ('url3', 2.2), ('url4', 'aaa')]

for url, latency_or_error
filter and sort:
    sorted(filter(lambda x: isinstance(x[1], float), lst1), key=lambda x: x[1])
    valid_lst1 = sorted(filter(lambda x: isinstance(x[1], float), lst1), key=lambda x: x[1])
    '\n'.join(_[0] for _ in valid_lst1)
    print('\n'.join(_[0] for _ in valid_lst1))
filter invalid
    print('\n'.join(_[1] for _ in filter(lambda x: isinstance(x[1], str), lst1)))
"""

# pylint: disable=invalid-name, broad-except, broad-exception-raised
# from about_time import about_time
from time import time
from typing import Tuple, Union

import aiohttp
import httpx
from httpx import Timeout
from loguru import logger

data = {"text": "Hello, world!", "source_lang": "EN", "target_lang": "ZH"}


def check_deeplx(
    url: str, timeout: Union[float, Timeout] = Timeout(6)
) -> Tuple[str, Union[float, str]]:
    """
    Check url for valid deeplx service.

    Args:
    ----
      url: dest url to check, must be a legit URL
      timeout: float or httpx.Timeout, default Timeout(6)

    Returns:
    -------
      (True, latency in second) if deeplx service present
      (False, message string) if not

    """
    try:
        # with about_time() as atime:
        then = time()
        _ = httpx.post(f"{url}/translate", json=data, timeout=timeout, verify=False)
        _.raise_for_status()
        check = "世界" in _.text or "你好" in _.text
        if not check:
            raise Exception(f"{url}/translate returns {_.text=}")

        # latency_or_error: Union[float, str] = round(atime.duration, 2)
        latency_or_error: Union[float, str] = round(time() - then, 2)
    except httpx.RequestError as exc:
        logger.trace(f"{exc=}")
        check, latency_or_error = False, str(exc)[:70]
    except Exception as exc:
        logger.trace(f"{exc=}")
        check, latency_or_error = False, str(exc)[:70]

    # return check, latency_or_error
    del check  # no use, we are returning url instead
    return url, latency_or_error


async def check_deeplx_async(
    url: str, timeout: Union[float, Timeout] = Timeout(6)
) -> Tuple[str, Union[float, str]]:
    """
    Check url for valid deeplx service with async.

    Args:
    ----
      url: dest url to check, must be a legit URL
      timeout: float or httpx.Timeout, default Timeout(6)

    Returns:
    -------
      (True, latency in second) if deeplx service present
      (False, message string) if not

    """
    try:
        # with about_time() as atime:
        then = time()
        # _ = httpx.post(f'{url}/translate', json=data)
        async with httpx.AsyncClient(verify=False) as client:
            _ = await client.post(
                f"{url}/translate",
                json=data,
                timeout=timeout,
            )
            _.raise_for_status()
        check = "世界" in _.text or "你好" in _.text
        if not check:
            raise Exception(f"{url}/translate returns {_.text=}")

        # latency_or_error: Union[float, str] = round(atime.duration, 2)
        latency_or_error: Union[float, str] = round(time() - then, 2)
    except httpx.ConnectTimeout:
        check, latency_or_error = False, "Timeout"
    except httpx.ReadTimeout:
        check, latency_or_error = False, "ReadTimeout"
    except Exception as exc:
        logger.trace(f"{url}, {exc=}")
        check, latency_or_error = False, str(exc)[:70]

    # return check, latency_or_error
    del check  # no use, we are returning url instead
    return url, latency_or_error


async def check_deeplx_async1(
    url: str, timeout: float = 6
) -> Tuple[str, Union[float, str]]:
    """
    Check url for valid deeplx service using aiohttp.

    Args:
    ----
      url: dest url to check, must be a legit URL
      timeout: float, default 6

    Returns:
    -------
      (True, latency in second) if deeplx service present
      (False, message string) if not

    """
    try:
        # with about_time() as atime:
        then = time()
        # _ = httpx.post(f'{url}/translate', json=data)
        # async with httpx.AsyncClient(verify=False) as client:
        async with aiohttp.ClientSession() as client:
            _ = await client.post(
                f"{url}/translate",
                json=data,
                timeout=timeout,
                ssl=False,
            )
            _.raise_for_status()
            text = await _.text()
        check = "世界" in text or "你好" in text
        if not check:
            raise Exception(f"{url}/translate returns {text=}")

        # latency_or_error: Union[float, str] = round(atime.duration, 2)
        latency_or_error: Union[float, str] = round(time() - then, 2)
    except TimeoutError:
        check, latency_or_error = False, "Timed out"
    except Exception as exc:
        logger.trace(f"{url}, {exc=}")
        check, latency_or_error = False, str(exc)[:70]

    # return check, latency_or_error
    del check  # no use, we are returning url instead
    return url, latency_or_error


if __name__ == "__main__":
    import asyncio
    import sys

    url_ = "".join(sys.argv[1:2])
    if not url_:
        url_ = "https://api.deeplx.org"
        url_ = "http://acone:8080"  # deeplx-urls?
        url_ = "http://acone:1188"
    # wake it up
    _ = check_deeplx(url_)
    print(check_deeplx(url_))

    print(asyncio.run(check_deeplx_async(url_)))
