import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def timed_stage(logger: logging.Logger, stage: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.info("%s took %.3fs", stage, time.perf_counter() - start)
