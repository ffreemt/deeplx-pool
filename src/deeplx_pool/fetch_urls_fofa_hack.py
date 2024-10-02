"""Fetch urls from fofa using fofa-hack."""
# pylint: disable=invalid-name, line-too-long, broad-exception-caught

from random import choice

from fofa_hack import fofa
from loguru import logger

query_def1 = '''"deepl translate api" && country="CN"'''
query_def2 = '''body='{"code":200,"message":"DeepL Free API, Developed by sjlleo and missuo. Go to /translate with POST. http://github.com/OwO-Network/DeepLX"}' && country="CN"'''
query_def3 = '''"welcome to deeplx" && country="CN"'''
# query_def = choice([query_def1, query_def2, query_def3])
queries = [query_def1, query_def2, query_def3]


def fetch_urls_fofa_hack(query="", endcount=10, proxies=None):
    """
    Fetch urls from fofa using fofa-hack.

    e.g. proxies={"https": "socks5://127.0.0.1:11080"}
    """
    if not query:
        query = choice(queries)
        logger.debug(f"{query=}")
    urls = []

    result_generator = fofa.api(query, endcount=endcount, proxy=proxies)

    for elm in result_generator:
        try:
            urls.extend(elm)
        except RuntimeError as exc:
            logger.error(exc)
        except Exception as exc:
            logger.error(exc)
    return urls
