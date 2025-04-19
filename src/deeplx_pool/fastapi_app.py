"""
Modified from deeplpro-tr\app.py.

curl -X POST "http://127.0.0.1:8000/translate" \
-H "Authorization: Bearer token123" \
-H "Content-Type: application/json" \
-d '{"text": "hello"}'

# note the double quotes
set TOKENS=["abc"]

refer also to https://github.com/snailyp/yeschat-reverse/blob/main/api/main.py
"""
# pylint: disable=broad-exception-caught, invalid-name

from itertools import cycle
import os
from pathlib import Path
import json
import subprocess
from time import sleep
from typing import Optional
from threading import Thread

import diskcache
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger

# from pydantic import BaseModel
from ycecream import y
import uvicorn

from deeplx_pool import __version__, deeplx_pool
from proc_file import proc_file

_ = Path.home() / ".diskcache" / "deeplx-sites"
cache = diskcache.Cache(_)

y.configure(sln=1, e=0)

DESC = """\
Authentication can be set via env var TOKENS,
e.g. export DXPOOL_TOKENS='["abc123", "linux1", "LINUXDO"]', but is not recommended in
the spirit of sharing.
"""

app = FastAPI(
    title="deeplx-pool",
    description=DESC,
    version=__version__,
)

# Define a list of valid tokens
# TOKENS = ["token123", "token456", "token789"]
# os.environ["TOKENS"] = json.dumps(["LINUXDO", "linuxdo"])

try:
    y(os.getenv("TOKENS"))
    _ = os.getenv("DXPOOL_TOKENS")
    TOKENS = json.loads(_.replace("'", '"'))  # type: ignore
except Exception as exc:
    y(exc)
    TOKENS = None

y(TOKENS)


def authenticate_token(authorization: Optional[str] = Header(None)):
    """Authenticate TOKENS if defined."""
    y(not TOKENS)

    # valid: ["token123", "token456", "token789"]
    # if env var TOKENS not defined or invalid, skip auth
    if not TOKENS:
        return

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization[len("Bearer ") :]
    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="Unauthorized")


# Landing page with "Welcome" message
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Return landing message 'Welcome to deeplx-pool!' (for fofa/shodan etc)."""
    html_content = """
    <html>
        <head>
            <title>Landing Page</title>
        </head>
        <body>
            <h1>Welcome to deeplx-urls</h1>
        </body>
    </html>
    """
    del html_content
    return "Welcome to deeplx-pool!"


@app.post("/")
async def fetch_urls(
    token: str = Depends(authenticate_token),  # pylint: disable=unused-argument
):
    """Return deeplx site urls."""
    try:
        _ = dict(cache.get("deeplx-sites")[:1])  # type: ignore
    except Exception as exc:
        logger.error(exc)
        _ = {"errors": str(exc)}
    return _


@app.post("/all")
async def fetch_all_urls(
    token: str = Depends(authenticate_token),  # pylint: disable=unused-argument
):
    """Return all deeplx site urls."""
    try:
        _ = dict(cache.get("deeplx-sites"))  # type: ignore
    except Exception as exc:
        logger.error(exc)
        _ = {"errors": str(exc)}
    return _


@app.get("/all")
async def fetch_all_urls_get(
    token: str = Depends(authenticate_token),  # pylint: disable=unused-argument
):
    """Return all deeplx site urls."""
    try:
        _ = dict(cache.get("deeplx-sites"))  # type: ignore
    except Exception as exc:
        logger.error(exc)
        _ = {"errors": str(exc)}
    return _


@app.post("/num")
async def post_num(
    token: str = Depends(authenticate_token),  # pylint: disable=unused-argument
):
    """Return all deeplx site urls."""
    try:
        _ = len(cache.get("deeplx-sites"))  # type: ignore
    except Exception as exc:
        logger.error(exc)
        _ = str(exc)
    return _


@app.get("/num")
async def get_num(
    token: str = Depends(authenticate_token),  # pylint: disable=unused-argument
):
    """Return all deeplx site urls."""
    try:
        _ = len(cache.get("deeplx-sites"))  # type: ignore
    except Exception as exc:
        logger.error(exc)
        _ = str(exc)
    return _


@app.post("/set")
async def fetch_n_urls(
    num: int = 0,
    token: str = Depends(authenticate_token),  # pylint: disable=unused-argument
):
    """Return deeplx site urls."""
    if num == 0:
        try:
            _ = dict(cache.get("deeplx-sites"))  # type: ignore
        except Exception as exc:
            logger.error(exc)
            _ = {"errors": str(exc)}
        return _

    num = max(num, 1)

    try:
        _ = dict(cache.get("deeplx-sites")[:num])  # type: ignore
    except Exception as exc:
        logger.error(exc)
        _ = {"errors": str(exc)}
    return _


@app.get("/set")
async def fetch_n_urls_get(
    num: int = 0,
    token: str = Depends(authenticate_token),  # pylint: disable=unused-argument
):
    """Return deeplx site urls."""
    if num == 0:
        try:
            _ = dict(cache.get("deeplx-sites"))  # type: ignore
        except Exception as exc:
            logger.error(exc)
            _ = {"errors": str(exc)}
        return _

    num = max(num, 1)
    try:
        _ = dict(cache.get("deeplx-sites")[:num])  # type: ignore
    except Exception as exc:
        logger.error(exc)
        _ = {"errors": str(exc)}
    return _


@app.get("/health", include_in_schema=False)
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy"}
    )


@app.head("/health")
async def health_head():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy"}
    )


def run_deeplx_pool_main():
    """Prep for Thread."""
    # while True:
    for count in cycle(range(5)):
        if count:
            y(count)
            deeplx_pool.main()
        else:  # run proc_file every 5 runs
            y(count)
            proc_file()
        sleep(1800)  # 30 minutes


if __name__ == "__main__":
    Thread(target=run_deeplx_pool_main).start()
    host = os.getenv("DXPOOL_HOST", "0.0.0.0")
    port = os.getenv("DXPOOL_PORT", "8787")
    try:
        port = int(port)
    except ValueError:
        port = 8787
    if port < 1024:
        logger.warning(f"port: {port} is reserved, setting to 8787")
        port = 8787

    # run proc_file.py first, default linuxdo216930.txt
    subprocess.run("uv run python proc_file.py", shell=True)

    uvicorn.run(app, host=host, port=port)
