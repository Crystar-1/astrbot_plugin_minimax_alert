"""
配置管理模块
封装插件配置项的读取操作
"""

from .whitelist import WhitelistManager
from astrbot.api import AstrBotConfig  # noqa: F401


class ConfigManager:
    """配置管理器"""

    def __init__(self, config: AstrBotConfig):
        """初始化配置管理器"""
        self._config = config
        self._whitelist_manager = WhitelistManager(
            whitelist=config.get("whitelist", [])
        )

    # ------------------- 配置读取 -------------------

    def get_whitelist(self) -> WhitelistManager:
        """获取白名单管理器"""
        return self._whitelist_manager

    def get_api_key(self) -> str:
        """获取 API Key"""
        return self._config.get("api_key", "")

    def get_region(self) -> str:
        """获取地区配置（国内/国际）"""
        return self._config.get("region", "国内")

    def get_group_id(self) -> str:
        """获取 Group ID（国际版必填）"""
        return self._config.get("group_id", "")

    def get_show_year(self) -> bool:
        """获取是否显示年份配置"""
        return self._config.get("show_year", False)

    def get_show_first_model_only(self) -> bool:
        """获取是否仅显示第一个模型配置"""
        return self._config.get("show_first_model_only", False)
