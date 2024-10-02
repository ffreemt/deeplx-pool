# deeplx-pool

deeplx url pool + REST API

## What it is
`deeplx-pool` gleans valid free deeplx services (about 30-70) from shodan and fofa locally (using `diskacache`).

## Usage
Install `uv` the way you like it, e.g.
```
pipx install uv
```
```
git clone https://github.com/ffreemt/deeplx-pool && cd deeplx-pool
uv python install 3.12
uv sync

uv run python -m deeplx_pool.deeplx_pool
# or simply execute `inv` if you have `invoke` installed
```
To retrieve the deeplx urls from `diskcache`:
```python
from pathlib import Path
import diskcache

cache = diskcache.Cache(Path.home() / ".diskcache" / "deeplx-sites")

urls = cache.get("deeplx-sites")
print(urls)
# [
#    ('http://107.150.100.170:8880', 0.76),
#    ('http://158.101.188.241:8088', 0.8),
#    ('http://167.99.205.173:8080', 0.83),
#    ('http://68.183.253.186:8080', 0.84),
#    ('http://195.170.172.119:8088', 0.86),...]
```

To quickly display the number of available urls:
```bash
uv run python -c 'from pathlib import Path; import diskcache; cache = diskcache.Cache(Path.home() / ".diskcache" / "deeplx-sites"); print(len(cache.get("deeplx-sites")))'
# 71
```