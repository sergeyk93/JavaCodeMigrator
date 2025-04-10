import logging
import sys
from contextlib import asynccontextmanager
import time
from logging import Logger
from pathlib import Path
from typing import Any, AsyncGenerator


class LogManager:
    @staticmethod
    def get_logger(name: str | None = None) -> Logger:
        if name is None:
            name = Path(__file__).stem
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        return logger


@asynccontextmanager
async def log_time(label: str, log: Logger) -> AsyncGenerator[None, Any]:
    start_time = time.perf_counter()
    log.info("%s started.", label)
    yield
    log.info("%s finished in %f seconds.", label, time.perf_counter() - start_time)
