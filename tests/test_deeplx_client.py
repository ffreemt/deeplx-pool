"""
Test deeplx_client.

Use -s or --capture=no e.g., pytest -s test_foobar.py to show output
"""

from loguru import logger
from deeplx_pool.deeplx_client import deeplx_client as cl


def test_deeplx_client_simple_sync():
    """Test deeplx_client_simple."""
    _ = cl("Test")
    logger.info(_)
    assert "测" in _

    _ = cl("Test", alternatives=1)
    logger.info(_)
    assert "试" in _
