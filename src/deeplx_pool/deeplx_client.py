"""
Fetch translation from api.deeplx.org and variants.

Unrelated to deeplx_tr.py

curl -X POST https://api.deeplx.org/translate -d '{
    "text": "Hello, world!",
    "source_lang": "de",
    "target_lang": "zh"
}'

example return:
{"code":200,"id":865910002,"data":"你好，世界","alternatives":["世界，你好","你好，世界！","大家好"]}
"""

# pylint: disable=invalid-name,too-many-branches, too-many-statements
import os
import sys
from typing import Union

import httpx
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
LINUXDO_API_TOKEN = os.getenv("LINUXDO_API_TOKEN")

if LINUXDO_API_TOKEN:
    deeplx_url = f"https://api.deeplx.org/{LINUXDO_API_TOKEN}/translate"
else:
    deeplx_url = "https://deeplx.dattw.eu.org/translate"
logger.trace(f"{deeplx_url=}")

def deeplx_client(
    text: str,
    source_lang: str = "",
    target_lang: str = "",
    alternatives: bool = False,
    url: Union[str, None] = None,
) -> str:
    """
    Translate via api.deeplx.org and variants.

    Unrelated to deeplx_tr.py

    Args:
    ----
    text: to be translated
    source_lang: source language (default auto)
    target_lang: default zh (chinese)
    alternatives: also output available alternatives if set (default False)
    url: deeplx api url, default https://api.deeplx.org/translate

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
            logger.warning("Unable to process {url=}, setting to ''.")
            url = ""

    url = url or os.getenv("DEEPLX_URL")

    assert url, f"{url=}, url must not be empty or None"

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

    try:
        resp = httpx.post(url, json=data)  # type: ignore
        resp.raise_for_status()
    except Exception as exc:
        logger.error(exc)
        raise

    try:
        res = resp.json().get("data")
        alt_output = resp.json().get("alternatives")
    except Exception as exc:
        logger.error(exc)
        raise

    if alternatives and alt_output:
        return f"{res} / {', '.join(alt_output)}"

    return res


def main():
    """Testrun, nothing fancy."""
    text = " ".join(sys.argv[1:])
    if not text:
        text = "test"

    print(f"{text=}")
    print(deeplx_client(text))
    print(deeplx_client(text, alternatives=True))


if __name__ == "__main__":
    main()
