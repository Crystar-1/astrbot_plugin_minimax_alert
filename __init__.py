import logging

try:
    from .main import MiniMaxAlertPlugin
    __all__ = ["MiniMaxAlertPlugin"]
except ImportError as e:
    __all__ = []
    logging.warning(f"无法加载 MiniMaxAlertPlugin: {e}")
