import logging
import os
from logging.handlers import RotatingFileHandler

# ==========================================
# 🎛️ 全局开关 (True = 打印到终端, False = 只写文件)
# ==========================================
ENABLE_CONSOLE_LOG = True

def setup_logger():
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "agent_runtime.log")

    logger = logging.getLogger("AgentSystem")
    # 如果开关是 False，这里甚至可以设为 WARNING 级别，只记录警告和错误
    logger.setLevel(logging.DEBUG if ENABLE_CONSOLE_LOG else logging.INFO)

    if not logger.handlers:
        # 1. 文件 Handler (永远记录完整日志，存起来方便以后排错)
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
        file_format = logging.Formatter('%(asctime)s | %(levelname)-7s | [%(name)s] | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        # 2. 控制台 Handler (受开关控制)
        if ENABLE_CONSOLE_LOG:
            console_handler = logging.StreamHandler()
            console_format = logging.Formatter('%(message)s')  # 调试时终端不需要太长，只保留核心信息
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)

    return logger

import time
from contextlib import contextmanager

@contextmanager
def log_node_execution(node_name: str):
    """耗时统计上下文管理器（工业级追踪接口）"""
    logger.info(f"--- 开始执行节点: {node_name} ---")
    start_time = time.time()
    try:
        yield
    except Exception as e:
        logger.error(f"节点 {node_name} 执行失败: {str(e)}", exc_info=True)
        raise
    finally:
        elapsed = time.time() - start_time
        logger.info(f"--- 节点 {node_name} 执行结束，耗时: {elapsed:.2f} 秒 ---")

logger = setup_logger()