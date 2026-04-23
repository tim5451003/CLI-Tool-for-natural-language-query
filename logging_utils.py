"""JSON-lines logging 工具：初始化 logger 與記錄分階段事件。"""

import json
import logging
from typing import Any, Dict


def setup_logger(log_file: str) -> logging.Logger:
    logger = logging.getLogger("wdq")
    logger.handlers = []
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)
    return logger


def log_event(logger: logging.Logger, stage: str, data: Dict[str, Any]) -> None:
    logger.info(json.dumps({"stage": stage, **data}, ensure_ascii=False))
