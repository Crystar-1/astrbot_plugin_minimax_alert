from .whitelist import WhitelistManager
from astrbot.api import AstrBotConfig


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config: AstrBotConfig):
        """
        初始化配置管理器
        
        Args:
            config: AstrBot 配置对象
        """
        self._config = config
        self._whitelist_manager = WhitelistManager(
            whitelist=config.get("whitelist", [])
        )
    
    def get_whitelist(self) -> WhitelistManager:
        """
        获取白名单管理器
        
        Returns:
            WhitelistManager 实例
        """
        return self._whitelist_manager
    
    def update_whitelist_config(self, whitelist: list[str]):
        """
        更新白名单配置并持久化
        
        Args:
            whitelist: 新的白名单列表
        """
        self._config["whitelist"] = whitelist
        self._whitelist_manager.set_whitelist(whitelist)
    
    def get_api_key(self) -> str:
        """
        获取 API Key
        
        Returns:
            API Key 字符串
        """
        return self._config.get("api_key", "")
    
    def get_region(self) -> str:
        """
        获取地区配置
        
        Returns:
            地区字符串（"国内" 或 "国际"）
        """
        return self._config.get("region", "国内")
    
    def get_group_id(self) -> str:
        """
        获取 Group ID
        
        Returns:
            Group ID 字符串
        """
        return self._config.get("group_id", "")
