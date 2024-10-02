"""
Fetch translation from api.deeplx.org and variants.

async version of deeplx_client

Unrelated to deeplx_tr.py

curl -X POST https://api.deeplx.org/translate -d '{
    "text": "Hello, world!",
    "source_lang": "de",
    "target_lang": "zh"
}'

example return:
{"code":200,"id":865910002,"data":"你好，世界","alternatives":["世界，你好","你好，世界！","大家好"]}
"""
# pylint: disable=invalid-name,too-many-branches, too-many-statements, too-many-arguments
import asyncio
import os
import sys
from typing import Union

import httpx
import nest_asyncio
from loguru import logger

nest_asyncio.apply()

deeplx_url = "https://api.deeplx.org"
client = httpx.AsyncClient(verify=False)

CONCURRENCY_LIMIT = 5
_ = os.getenv("CONCURRENCY_LIMIT")
if _ is not None:
    try:
        CONCURRENCY_LIMIT = int(os.getenv("CONCURRENCY_LIMIT"))  # type: ignore
    except (TypeError, ValueError):
        ...  # default 5 as above
    if CONCURRENCY_LIMIT < 1:
        CONCURRENCY_LIMIT = 5  # if < 1, set to 5

SEMAPHORE = asyncio.Semaphore(CONCURRENCY_LIMIT)


async def deeplx_client_async(
    text: str,
    source_lang: str = "",
    target_lang: str = "",
    alternatives: bool = False,
    url: Union[str, None] = None,
    # sem=SEMAPHORE,
) -> str:
    """
    Translate via api.deeplx.org and variants.

    async version of deeplx_client

    Unrelated to deeplx_tr.py

    Args:
    ----
    text: to be translated
    source_lang: source language (default auto)
    target_lang: default zh (chinese)
    alternatives: also output available alternatives if set (default False)
    url: deeplx api url, default https://api.deeplx.org/translate
    sem: semaphore, default 5

    Returns:
    -------
    translation

    """
    # url = deeplx_url
    # if os.getenv("DEEPLX_URL") is not None:

    if url is None:
        url = deeplx_url
    else:
        try:
            url = url.strip()
        except Exception:
            logger.warning(f"Unable to process {url=}, setting to {deeplx_url}.")
            url = deeplx_url

    url = url or os.getenv("DEEPLX_URL")

    # assert url, f"{url=}, url must not be empty or None"
    if not url:
        logger.warning(f" {url=}, setting to {deeplx_url}")
        url = deeplx_url

    try:
        text = str(text).strip()
    except Exception as exc:
        logger.error(exc)
        raise
    if not text:
        logger.warning("empty input, nothing to do, return ''.")
        return ""

    try:
        source_lang = source_lang.strip()
    except Exception:
        source_lang = ""
    try:
        target_lang = target_lang.strip()
    except Exception:
        target_lang = "zh"

    if source_lang.lower() in ["chinese", "zhong", "zhongwen"]:
        source_lang = "zh"
    if target_lang.lower() in ["chinese", "zhong", "zhongwen"]:
        target_lang = "zh"

    if source_lang.lower() in ["english", "eng"]:
        source_lang = "en"
    if target_lang.lower() in ["english", "eng"]:
        target_lang = "en"

    if source_lang.lower() in ["deutsch", "german", "ger"]:
        source_lang = "de"
    if target_lang.lower() in ["deutsch", "german", "ger"]:
        target_lang = "de"

    if source_lang in [""] and target_lang in [""]:
        target_lang = "zh"
    logger.trace(f"{source_lang=}, {target_lang=}")

    if source_lang in ["en"] and target_lang in [""]:
        source_lang = "zh"
    if source_lang in ["zh"] and target_lang in [""]:
        source_lang = "en"

    logger.trace(f"{text=}")
    logger.trace(f"{source_lang=}, {target_lang=}")

    if source_lang == target_lang:
        return text

    data = {
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }

    logger.trace(f"{data=}")
    logger.trace(f"url = {url}/translate")

    # async with semaphore:
    # if True:
    # async with sem:
    try:
        resp = await client.post(f"{url}/translate", json=data)  # type: ignore
        resp.raise_for_status()
    except Exception as exc:
        # will be handled downstream
        logger.error(exc)
        raise

    logger.trace(f"{resp=}")

    try:
        res = resp.json().get("data")
        alt_output = resp.json().get("alternatives")
    except Exception as exc:
        # will be handled downstream
        logger.error(exc)
        raise

    logger.trace(f"{res=}")

    if alternatives and alt_output:
        return f"{res} / {', '.join(alt_output)}"

    return res


async def main():
    """Testrun, nothing fancy."""
    text = " ".join(sys.argv[1:])
    if not text:
        text = "test"

    print(f"{text=}")
    _ = await asyncio.gather(
        deeplx_client_async(text),
        deeplx_client_async(text, alternatives=True),
        deeplx_client_async("hello world"),
        deeplx_client_async("hello world", alternatives=True),
        return_exceptions=True,
    )
    print(_)


if __name__ == "__main__":
    asyncio.run(main())
