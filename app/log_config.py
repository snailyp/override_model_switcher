import logging
import colorlog


def setup_logger(name):
    # 创建 ColoredFormatter
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(asctime)s%(reset)s %(white)s%(name)s%(reset)s %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    # 创建一个 StreamHandler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    # 创建 logger
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)  # 设置默认日志级别，可以根据需要调整
    return logger
