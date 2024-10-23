"""
Define invoke tasks.

inv -l
invoke --list
invoke build

invoke --help build

"""

from invoke import task


@task(
    default=True,
)
def scrape_deeplx(c):
    """Scrape shodan/foda ip."""
    # c.run(r"python src\deeplx_pool\scrape_deeplx_shodan.py")
    # c.run("rye run python -m deeplx_pool.scrape_deeplx_shodan")
    # c.run("rye run python -m deeplx_pool.deeplx_pool")
    c.run("uv run python -m deeplx_pool.deeplx_pool")


@task()
def proc_file(c):
    """Run python proc_static.py, inv proc-static."""
    c.run("uv run python proc_file.py")


@task()
def fastapi(c):
    """Run uvicorn with fastapi: nodemon -w src/deeplx_pool/fastapi_app.py -x uv run python -m deeplx_pool.fastapi_app."""
    c.run(
        "nodemon -w src/deeplx_pool/fastapi_app.py -x uv run python -m deeplx_pool.fastapi_app"
    )
